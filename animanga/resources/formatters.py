from mautrix.types import TextMessageEventContent, MessageType, Format
from mautrix.util.config import BaseProxyConfig

from .datastructures import (
    SearchResult,
    AniMangaData,
    media_formats
)


class Formatter:
    width = 230
    height = 325

    def __init__(self, config: BaseProxyConfig | None) -> None:
        self.config = config

    async def prepare_message(
            self,
            data: AniMangaData,
            other: list[SearchResult]
    ) -> TextMessageEventContent:
        """
        Prepare the final message based on the parsed results from AniList API
        :param data: AniMangaData object
        :param other: list of initial search results
        :return: text message for the user
        """
        # Title and description
        header = await self._get_titles(data)
        body = await self._get_titles(data, False)

        # Score
        header += await self._get_score(data)
        body += await self._get_score(data, False)

        # Description
        main_section = await self._get_description(data)
        body += await self._get_description(data, False)

        # Image
        poster = await self._get_poster(data)
        body += await self._get_poster(data, False)

        # Details section
        # Other titles
        details_section = await self._get_other_titles(data)
        body += await self._get_other_titles(data, False)

        # Format
        details_section += await self._get_format(data)
        body += await self._get_format(data, False)

        # Status and next episode date
        details_section += await self._get_status_next_episode(data)
        body += await self._get_status_next_episode(data, False)

        # Dates, season
        details_section += await self._get_dates_season(data)
        body += await self._get_dates_season(data, False)

        # Studios
        details_section += await self._get_studios(data)
        body += await self._get_studios(data, False)

        # Authors
        details_section += await self._get_authors(data)
        body += await self._get_authors(data, False)

        # Links
        details_section += await self._get_links(data)
        body += await self._get_links(data, False)

        # Genres
        details_section += await self._get_genres(data)
        body += await self._get_genres(data, False)

        # Tags
        details_section += await self._get_tags(data)
        body += await self._get_tags(data, False)

        # Links section
        links_section = ""
        if data.relations or len(other) > 1:
            # Related entries
            links_p1 = await self._get_related_entries(data)
            body += await self._get_related_entries(data, False)

            # Other results
            links_p2 = await self._get_other_results(data, other)
            body += await self._get_other_results(data, other, False)

            links_section = await self._get_links_section(links_p1, links_p2)

        body += "> **Results from AniList**"
        html = (
            "<blockquote>"
            f"<div>{header}</div>"
            f"<div>{await self._get_details("SYNOPSIS", main_section)}</div>"
            f"<div>{await self._get_details("POSTER", poster)}</div>"
            f"<div>{await self._get_details("DETAILS", details_section)}</div>"
            f"<div>{await self._get_details("LINKS", links_section)}</div>"
            "<p><b><sub>"
            f"Results from {"MyAnimeList" if self.config["use_mal_api"] else "AniList"}"
            "</sub></b></p>"
            "</blockquote>"
        )

        return TextMessageEventContent(
            msgtype=MessageType.NOTICE,
            format=Format.HTML,
            body=body,
            formatted_body=html
        )

    async def _get_details(self, title: str, content: str) -> str:
        if not content or not title:
            return ""
        return f"<details><summary><b>{title} </b></summary>{content}</details>"

    async def _get_link(self, url: str, text: str, is_html: bool = True) -> str:
        """
        Return a link as HTML or Markdown
        :param url: address
        :param text: displayed text
        :param is_html: True for HTML, False for Markdown
        :return: formatted link
        """
        # HTML
        if is_html:
            return f"<a href=\"{url}\">{text}</a>"

        # Markdown
        return f"[{text}]({url})"

    async def _get_titles(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get title section of formatted message
        :param title_ro: Romaji title
        :param title_en: English title
        :param al_id: Anilist ID
        :param is_html: True for HTML, False for Markdown
        :return: Formatted title section
        """
        media_type = data.type.lower() if data.type else "anime"
        # Title and description - panel 1
        title = data.title_en if data.title_en else data.title_ro
        al_url = (
            f"https://myanimelist.net/{media_type}/{data.id}"
            if self.config["use_mal_api"] else f"https://anilist.co/{media_type}/{data.id}"
        )
        mal_url = f"https://myanimelist.net/{media_type}/{data.id_mal}"
        result = ""

        # HTML
        if is_html:
            result += "<h3>"
            result += f"{await self._get_link(al_url, f"{title}")}"
            if data.id_mal:
                result += f" <sup>({await self._get_link(mal_url, "MAL")})</sup>"
            if data.nsfw:
                result += " 🔞"
            result += "</h3>"
            return result

        # Markdown
        result += f"> ### {await self._get_link(al_url, title, False)}"
        if data.id_mal:
            result += f" ({await self._get_link(mal_url, "MAL", False)})"
        if data.nsfw:
            result += " 🔞"
        result += "  \n>  \n"
        return result

    async def _get_score(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get formatted scores
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: formatted score string
        """
        result = ""
        score = None
        if data.average_score:
            score = float(data.average_score) / 100
        elif data.mean_score:
            score = float(data.mean_score) / 100
        if score:
            vote_data = f"⭐ {score}/10"
            if data.votes:
                vote_data += f" | 👤 {data.votes:_} votes".replace("_", " ")
            if data.favorites:
                vote_data += f" | ❤️ {data.favorites:_} favorites".replace("_", " ")
            if is_html:
                result = f"<blockquote><b>Score:</b> {vote_data}</blockquote>"
            else:
                result = f"> > **Score**: {vote_data}  \n>  \n"
        return result

    async def _get_description(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get the description with trimmed whitespace between paragraphs
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: formatted description
        """
        result = ""
        if data.description:
            description = data.description.replace('<br><br>', '<br>')
            if is_html:
                result = f"<p>{description}</p>"
            else:
                result = (
                    f"> {description
                         .replace('\r', '')
                         .replace('\n', '')
                         .replace('<br>', '  \n> ')}  \n>  \n"
                )
        return result

    async def _get_image(
        self,
        src: str,
        alt: str = "",
        size: tuple[int, int] = (0, 0),
        is_html: bool = True
    ) -> str:
        """
        Get link
        :param src: source url
        :param alt: alternative text
        :param size: width and height
        :param is_html: True for HTML, False for Markdown
        :return: formatted image
        """
        width = f"width=\"{size[0]}\" " if size[0] else ""
        height = f"height=\"{size[1]}\" " if size[1] else ""
        if is_html:
            return f"<img src=\"{src}\" alt=\"{alt}\" {width}{height}/>"
        return f"![{alt}]({src})"

    async def _get_poster(self, data: AniMangaData, is_html: bool = True) -> str:
        # Image
        if not data.image:
            return ""
        image = await self._get_image(
                data.image,
                f"Poster for {data.title_en if data.title_en else data.title_ro}",
                (self.width, self.height),
                is_html
            )
        if is_html:
            return image
        return f"{image}  \n>  \n"

    async def _get_other_titles(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get alternative titles
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Other titles section
        """
        other_titles = (
            f"{f'{data.title_ro}, ' if data.title_en else ''}"
            f"{data.title_ja if data.title_ja else ''}"
        )
        if not other_titles:
            return ""
        if is_html:
            return f"<blockquote><b>Other titles:</b> {other_titles}</blockquote>"
        return f"> > **Other titles:** {other_titles}  \n>  \n"

    async def _get_format(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get entry format data
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Format section
        """
        result = ""
        if data.format:
            media_format = data.format
            if data.episodes:
                media_format += f" | {data.episodes} episode{'s' if data.episodes > 1 else ''}"
                if data.duration:
                    duration = data.duration
                    media_format += f" ({duration}{' per episode' if data.episodes > 1 else ''})"
            if data.volumes:
                media_format += f" | {data.volumes} volumes"
            if data.chapters:
                media_format += f" | {data.chapters} chapters"
            if is_html:
                result = f"<blockquote><b>Format:</b> {media_format}</blockquote>"
            else:
                result = f"> > **Format**: {media_format}  \n>  \n"
        return result

    async def _get_status_next_episode(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get information about the status and the next upcoming episode
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Status section
        """
        result = ""
        broadcast = ""
        if data.next_episode_num and data.next_episode_date:
            broadcast = f" | Episode {data.next_episode_num} on {data.next_episode_date}"
        if data.status:
            if is_html:
                result = f"<blockquote><b>Status:</b> {data.status}{broadcast}</blockquote>"
            else:
                result = f"> > **Status:** {data.status}{broadcast}  \n>  \n"
        return result

    async def _get_dates_season(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get information about dates of release
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Date section
        """
        result = ""
        released = ""
        if data.start_date:
            if data.start_date == data.end_date or data.format == media_formats["MOVIE"]:
                released += f"{data.start_date}"
            else:
                released += f"{data.start_date} to {data.end_date if data.end_date else '?'}"
        if data.season and data.season_year:
            if released:
                released += f" | {data.season} {data.season_year}"
            else:
                released = f"{data.season} {data.season_year}"
        if released:
            if is_html:
                result = f"<blockquote><b>Released:</b> {released}</blockquote>"
            else:
                result = f"> > **Released:** {released}  \n>  \n"
        return result

    async def _get_studios(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get information about studios
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Studios section
        """
        result = ""
        if data.studios:
            studios = ", ".join([
                    await self._get_link(
                        f"https://myanimelist.net/anime/producer/{studio[1]}"
                        if self.config["use_mal_api"]
                        else f"https://anilist.co/studio/{studio[1]}",
                        studio[0],
                        is_html
                    )
                    for studio in data.studios
                ])
            other_studios = (
                f" + {data.studio_number} other{'s' if data.studio_number > 1 else ''}"
                if data.studio_number else ""
            )
            if is_html:
                result = f"<blockquote><b>Studios:</b> {studios}{other_studios}</blockquote>"
            else:
                result = f"> > **Studios:** {studios}{other_studios}  \n>  \n"
        return result

    async def _get_authors(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get list of genres related to an entry
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Genres section
        """
        if not data.authors:
            return ""
        authors = []
        for author in data.authors:
            link = await self._get_link(
                f"https://myanimelist.net/people/{author[2]}"
                if self.config["use_mal_api"]
                else f"https://anilist.co/staff/{author[2]}",
                author[0],
                is_html
            )
            authors.append(f"{link} ({author[1]})")
        authors_str = ", ".join(authors)
        if is_html:
            result = f"<blockquote><b>Authors:</b> {authors_str}</blockquote>"
        else:
            result = f"> > **Authors:** {authors_str}  \n>  \n"
        return result

    async def _get_links(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get external links for an entry
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: External links section
        """
        result = ""
        if data.links or data.trailer:
            links = ""
            text = "🎬 <b>TRAILER</b>" if is_html else "🎬 **TRAILER**"
            if data.trailer and data.trailer[0] == "youtube" and data.trailer[1]:
                yt_link = f"https://www.youtube.com/watch?v={data.trailer[1]}"
                links += await self._get_link(yt_link, text, is_html)
            if data.links:
                links = links + ", " if links else links
                links += ", ".join(
                    [await self._get_link(link[1], link[0], is_html) for link in data.links]
                )
            if is_html:
                result = f"<blockquote><b>External links:</b> {links}</blockquote>"
            else:
                result = f"> > **External links:** {links}  \n>  \n"
        return result

    async def _get_genres(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get list of genres related to an entry
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Genres section
        """
        result = ""
        media_type = data.type.lower() if data.type else "anime"
        if data.genres:
            genres = ", ".join([
                await self._get_link(
                    f"https://myanimelist.net/{media_type}/genre/{genre[1]}"
                    if self.config["use_mal_api"]
                    else f"https://anilist.co/search/{media_type}/{genre[0].replace(' ', '%20')}",
                    genre[0],
                    is_html
                ) for genre in data.genres
            ])
            if is_html:
                result = f"<blockquote><b>Genres:</b> {genres}</blockquote>"
            else:
                result = f"> > **Genres:** {genres}  \n>  \n"
        return result

    async def _get_tags(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get list of tags related to an entry
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Tags section
        """
        result = ""
        media_type = data.type.lower() if data.type else "anime"
        if data.tags:
            tags = ", ".join([
                await self._get_link(
                    f"https://myanimelist.net/{media_type}/genre/{tag[1]}"
                    if self.config["use_mal_api"] else
                    f"https://anilist.co/search/{media_type}?genres={tag[0].replace(' ', '%20')}",
                    tag[0],
                    is_html
                ) for tag in data.tags
            ])
            if is_html:
                result = f"<blockquote><b>Tags:</b> {tags}</blockquote>"
            else:
                result = f"> > **Tags:** {tags}  \n>  \n"
        return result

    async def _get_related_entries(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get list of related entries
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Related entries section
        """
        result = ""
        header = "<b>Related entries:</b>" if is_html else "> **Related entries:**  \n>  \n"
        if data.relations:
            result += header
            for i, rel in enumerate(data.relations):
                base_url = rel[1].media_type.lower()
                al_link = await self._get_link(
                    f"https://myanimelist.net/{base_url}/{rel[1].id}"
                    if self.config["use_mal_api"]
                    else f"https://anilist.co/{base_url}/{rel[1].id}",
                    rel[1].title_en if rel[1].title_en else rel[1].title_ro,
                    is_html
                )
                mal_link = ""
                if rel[1].id_mal:
                    mal_link = await self._get_link(
                        f"https://myanimelist.net/{base_url}/{rel[1].id_mal}",
                        "MAL",
                        is_html
                    )

                if is_html:
                    result += f"<blockquote>[{rel[0]}]<br>{i + 1}. {al_link}"
                    if mal_link:
                        result += f" <sup>({mal_link})</sup>"
                    result += "</blockquote>"
                else:
                    result += f"> > {i + 1}. {al_link}"
                    if mal_link:
                        result += f" ({mal_link})"
                    result += f" [{rel[0]}]  \n>  \n"
        return result

    async def _get_other_results(
            self,
            data: AniMangaData,
            other: list[SearchResult],
            is_html: bool = True
    ) -> str:
        """
        Get list of other results for current query
        :param data: AniMangaData
        :param other: list of other search results for the current query
        :param is_html: True for HTML, False for Markdown
        :return: Other results section
        """
        result = ""
        media_type = data.type.lower() if data.type else "anime"
        header = "<b>Other results:</b>" if is_html else "> **Other results:**  \n>  \n"
        if len(other) > 1:
            result += header
            # Omit the first because that's the main result
            for i, elem in enumerate(other[1:], start=1):
                al_title = elem.title_en if elem.title_en else elem.title_ro
                al_link = await self._get_link(
                    f"https://myanimelist.net/{media_type}/{elem.id}"
                    if self.config["use_mal_api"]
                    else f"https://anilist.co/{media_type}/{elem.id}",
                    al_title,
                    is_html
                )
                mal_link = ""
                if elem.id_mal:
                    mal_link = await self._get_link(
                        f"https://myanimelist.net/{media_type}/{elem.id_mal}",
                        "MAL",
                        is_html
                    )

                if is_html:
                    result += f"<blockquote>{i}. {al_link}"
                    if mal_link:
                        result += f" <sup>({mal_link})</sup>"
                    result += "</blockquote>"
                else:
                    result += f"> > {i}. {al_link}"
                    if mal_link:
                        result += f" ({mal_link})"
                    result += "  \n>  \n"
        return result

    async def _get_links_section(self, col1: str, col2: str) -> str:
        col1 = f"<div>{col1}</div>" if col1 else ""
        col2 = f"<div>{col2}</div>" if col2 else ""
        return f"{col1}{col2}"
