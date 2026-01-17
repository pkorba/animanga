import mimetypes
from datetime import datetime
from typing import Type, Any

from aiohttp import ClientTimeout, ClientError
from mautrix.errors import MatrixResponseError
from mautrix.types import TextMessageEventContent, MessageType, Format
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command

from .resources import queries
from .resources.datastructures import (
    SearchResult,
    AniMangaData,
    media_formats,
    statuses,
    relation_types,
    seasons,
    months
)


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("max_results")
        helper.copy("max_relations")


class AniMangaBot(Plugin):
    url = "https://graphql.anilist.co"
    headers = {
        "User-Agent": "AniMangaBot/1.1.0"
    }

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

    @command.new(
        name="anime",
        help="Search for titles of anime on AniList",
        require_subcommand=False,
        arg_fallthrough=False
    )
    @command.argument("title", pass_raw=True, required=True)
    async def anime(self, evt: MessageEvent, title: str) -> None:
        await evt.mark_read()
        title = title.strip()
        if not title:
            await evt.reply(
                "> **Usage:**  \n"
                "> !anime <title>"
            )
            return
        await self.al_message_handler(evt, title, "ANIME")

    @command.new(
        name="manga",
        help="Search for titles of manga on AniList",
        require_subcommand=False,
        arg_fallthrough=False
    )
    @command.argument("title", pass_raw=True, required=True)
    async def manga(self, evt: MessageEvent, title: str) -> None:
        await evt.mark_read()
        title = title.strip()
        if not title:
            await evt.reply(
                "> **Usage:**  \n"
                "> !manga <title>"
            )
            return
        await self.al_message_handler(evt, title, "MANGA")

    async def al_message_handler(self, evt: MessageEvent, title: str, media_type: str) -> None:
        """
        Commands the process of creating message for the user
        :param evt: user's message event
        :param title: anime or manga title
        :param media_type: type of medium
        """
        # Search for entries by title
        try:
            json = {
                "query": queries.general,
                "variables": {
                    "search": title,
                    "perPage": self.get_max_results(),
                    "type": media_type,
                }
            }
            results_json = await self._al_get_results(json)
        except ClientError as e:
            await evt.reply(f"> {e}")
            return
        # Parse results
        results = await self._al_parse_results(results_json)
        if not results:
            await evt.reply(f"Failed to find results for *{title}*")
            return

        # Get detailed information about the first entry from the previous query
        query = queries.anime if media_type == "ANIME" else queries.manga
        try:
            json = {
                "query": query,
                "variables": {
                    "id": results[0].id
                }
            }
            main_result_json = await self._al_get_results(json)
        except ClientError as e:
            await evt.reply(f"> {e}")
            return
        # Parse the detailed result
        main_result = await self._al_parse_main_result(main_result_json)
        if not main_result:
            await evt.reply(
                f"> There happened to be a problem while fetching results for **{title}**"
            )
            return
        # Get the thumbnail
        if main_result.image:
            main_result.image = await self.get_matrix_image_url(main_result.image)

        # Prepare and send message
        content = await self._prepare_message(main_result, results)
        if content:
            await evt.reply(content)
        else:
            await evt.reply("> There happened to be a problem while preparing the summary.")

    async def _al_get_results(self, json: Any) -> Any:
        """
        Hit AniList API to get the results.
        :param json: structure containing the query and variables for the query
        :return: AniList API response
        """
        timeout = ClientTimeout(total=20)
        try:
            response = await self.http.post(
                self.url,
                json=json,
                headers=self.headers,
                timeout=timeout,
                raise_for_status=True
            )
            return await response.json()
        except ClientError as e:
            self.log.error(f"Connection to AniList API failed: {e}")
            raise ClientError("Connection to AniList API failed.") from e

    async def _al_parse_results(self, data: Any) -> list[SearchResult]:
        """
        Parse the initial results from AniList API
        :param data: AniList API response
        :return: list of search results
        """
        if data.get("errors", None):
            self.log.error(
                "Error parsing results: "
                f"{'; '.join([error.get('message', '') for error in data['errors']])}"
            )
            return []
        results: list[SearchResult] = []
        for result in data["data"]["Page"]["media"]:
            sr = SearchResult(
                id=result["id"],
                id_mal=result["idMal"],
                title_ro=result["title"]["romaji"],
                title_en=result["title"]["english"]
            )
            results.append(sr)
        return results

    async def _al_parse_main_result(self, data: Any) -> AniMangaData | None:
        """
        Parse the main result from AniList API
        :param data: AniList API response
        :return: AniMangaData object or None if there are errors
        """
        if data.get("errors", None):
            self.log.error(
                f"Error parsing results: "
                f"{'; '.join([error.get('message', '') for error in data['errors']])}"
            )
            return None
        data = data["data"]["Media"]
        relations = await self._parse_relations(data["relations"]["edges"])
        result = AniMangaData(
            id=data["id"],
            id_mal=data["idMal"],
            title_ro=data["title"].get("romaji", ""),
            title_en=data["title"].get("english", ""),
            title_ja=data["title"].get("native", ""),
            type=data["type"],
            image=data["coverImage"].get("large", ""),
            start_date=await self._parse_date(data, "startDate"),
            end_date=await self._parse_date(data, "endDate"),
            description=await self._parse_desctiption(data),
            average_score=data["averageScore"],
            mean_score=data["meanScore"],
            # Number of votes is the sum of votes of each score. API doesn't provide the total value
            votes=sum(score["amount"] for score in data["stats"].get("scoreDistribution", [])),
            favorites=data["favourites"],
            nsfw=data["isAdult"],
            format=media_formats.get(data["format"], data["format"]),
            status=statuses.get(data["status"], data["status"]),
            genres=data["genres"],
            # Do not include tags that are marked as spoilers
            tags=[tag["name"] for tag in data["tags"] if not tag["isMediaSpoiler"]],
            relations=relations[:self.get_max_relations()],
            links=[(link["site"], link["url"]) for link in data["externalLinks"]],
        )
        if result.type == "ANIME":
            studios, studio_number = await self._parse_studios(data)
            result.episodes = data["episodes"]
            result.season = seasons.get(data["season"], data["season"])
            result.season_year = data["seasonYear"]
            result.next_episode_num = (
                data["nextAiringEpisode"].get("episode", 0)
                if data["nextAiringEpisode"] else None
            )
            result.next_episode_date = await self._parse_next_airing_episode(data)
            result.duration = data["duration"]
            result.studios = studios
            result.studio_number = studio_number
            result.trailer = (
                (data["trailer"].get("site", ""), data["trailer"].get("id", ""))
                if data["trailer"] else ()
            )
            result.volumes = 0
            result.chapters = 0
        else:
            result.episodes = 0
            result.season = ""
            result.season_year = 0
            result.next_episode_num = 0
            result.next_episode_date = ""
            result.duration = 0
            result.studios = set()
            result.studio_number = 0
            result.trailer = ()
            result.volumes = data["volumes"]
            result.chapters = data["chapters"]
        return result

    async def _parse_relations(self, relations_raw: Any) -> list[tuple[Any, SearchResult]]:
        """
        Sort relation types in order defined in relation_types dictionary.
        :param relations_raw: raw list od relations from API
        :return: sorted list of relations
        """
        # The default tuple for nonexistent relationType uses dict length
        # in order to put it at the end of the list
        relations = [
            (
                relation_types.get(relation["relationType"], [relation["relationType"].title()])[0],
                SearchResult(
                    id=relation["node"]["id"],
                    id_mal=relation["node"]["idMal"],
                    title_en=relation["node"]["title"].get("english", ""),
                    title_ro=relation["node"]["title"].get("romaji", ""),
                    media_type=relation["node"]["type"],
                )
            ) for relation in sorted(
                relations_raw,
                key=lambda rel: relation_types.get(
                    rel["relationType"],
                    ("", len(relation_types))
                )[1]
            )
        ]
        return relations

    async def _parse_desctiption(self, data: Any) -> str:
        """
        Remove the so-called "Notes" section in the description
        because it makes the summary unnecessarily long
        :param data: JSON data from API
        :return: clean description
        """
        description = ""
        if data["description"]:
            description_separator = "Notes:" if "Notes:" in data["description"] else "Note:"
            description = data["description"].split(description_separator)[0]
        return description

    async def _parse_date(self, data: Any, date_key: str) -> str:
        """
        Convert date from JSON to string where date format looks like following: 1 Apr 2137
        :param data: JSON data from API
        :param date_key: dictionary key of date in JSON data
        :return: formatted date
        """
        return (
            f"{str(data[date_key]['day']) + ' ' if data[date_key]['day'] else ''}"
            f"{months.get(data[date_key]['month']) + ' ' if data[date_key]['month'] else ''}"
            f"{data[date_key]['year'] if data[date_key]['year'] else ''}"
        )

    async def _parse_next_airing_episode(self, data: Any) -> str | None:
        """
        Get date and time for the next airing episode
        :param data: JSON data from API
        :return: formatted date
        """
        next_episode_date = None
        if data["nextAiringEpisode"] and data["nextAiringEpisode"].get("airingAt", 0):
            next_episode_date = datetime.fromtimestamp(
                data["nextAiringEpisode"]["airingAt"]
            ).strftime("%A, %-d %b %Y, %H:%M")
        return next_episode_date

    async def _parse_studios(self, data: Any) -> tuple[set[Any], int]:
        """
        Get list of studios and number of studios minus main studios
        :param data: JSON data from API
        :return: list of studios, number of studios
        """
        studios = set()
        studio_number = 0
        if data["studios"]["edges"]:
            # Only include main studio. AniList groups animation studios with producers here
            studios = {
                (studio["node"].get("name", ""), studio["node"].get("id", 0))
                for studio in data["studios"]["edges"] if studio["isMain"]
            }
            if not studios:
                first_producer = data["studios"]["edges"][0]
                studios = {
                    (first_producer["node"].get("name", ""), first_producer["node"].get("id", 0))
                }
            studio_number = len(data["studios"]["edges"]) - len(studios)
        return studios, studio_number

    async def _prepare_message(
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
        body = ""

        # Main table
        # Title and description
        main_col1 = ""
        main_col1 += await self._get_titles(data)
        body += await self._get_titles(data, False)

        # Score
        main_col1 += await self._get_score(data)
        body += await self._get_score(data, False)

        # Description
        main_col1 += await self._get_desctiption(data)
        body += await self._get_desctiption(data, False)

        main_col1 = f"<td>{main_col1}</td>"
        # Image
        if data.image:
            title = data.title_en if data.title_en else data.title_ro
            main_table = (
                f"<table><tr>{main_col1}"
                f"<td>{await self._get_image(
                    data.image,
                    f"Poster for {title}",
                    (0, 230)
                )}</td></tr></table>"
            )
            body += (
                f"> {await self._get_image(data.image, f"Poster for {title}", (0, 230), False)}"
                "  \n>  \n"
            )
        else:
            main_table = f"<table><tr>{main_col1}</tr></table>"

        # Details table
        # Other titles
        details_content = await self._get_other_titles(data)
        body += await self._get_other_titles(data, False)

        # Format
        details_content += await self._get_format(data)
        body += await self._get_format(data, False)

        # Status and next episode date
        details_content += await self._get_status_next_episode(data)
        body += await self._get_status_next_episode(data, False)

        # Dates, season
        details_content += await self._get_dates_season(data)
        body += await self._get_dates_season(data, False)

        # Studios
        details_content += await self._get_studios(data)
        body += await self._get_studios(data, False)

        # Links
        details_content += await self._get_links(data)
        body += await self._get_links(data, False)

        # Genres
        details_content += await self._get_genres(data)
        body += await self._get_genres(data, False)

        # Tags
        details_content += await self._get_tags(data)
        body += await self._get_tags(data, False)

        details_table = (
            "<div>"
            "<details><summary><b>DETAILS</b></summary>"
            f"<table><tr><td>{details_content}</td></tr></table>"
            "</details>"
            "</div>"
        )

        # Links table
        links_table = ""
        is_links = False
        if data.relations or len(other) > 1:
            is_links = True
        if is_links:
            # Related entries
            links_col1 = f"<td>{await self._get_related_entries(data)}</td>"
            body += await self._get_related_entries(data, False)

            # Other results
            links_col2 = f"<td>{await self._get_other_results(data, other)}</td>"
            body += await self._get_other_results(data, other, False)

            links_table = (
                "<div>"
                "<details><summary><b>LINKS</b></summary>"
                f"<table><tr>"
                f"{links_col1 if links_col1 else ""}"
                f"{links_col2 if links_col2 else ""}"
                f"</tr></table>"
                f"</details>"
                f"</div>"
            )

        body += "> **Results from AniList**"
        html = (
            "<blockquote>"
            f"{main_table}"
            f"{details_table}"
            f"{links_table}"
            "<p><b><sub>Results from AniList</sub></b></p>"
            "</blockquote>"
        )

        return TextMessageEventContent(
            msgtype=MessageType.NOTICE,
            format=Format.HTML,
            body=body,
            formatted_body=html
        )

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
        al_url = f"https://anilist.co/{media_type}/{data.id}"
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
            score = float(data.average_score) / 10
        elif data.mean_score:
            score = float(data.mean_score) / 10
        if score:
            vote_data = f"⭐ {score}/10"
            if data.votes:
                vote_data += f" | 👤 {data.votes} votes"
            if data.favorites:
                vote_data += f" | ❤️ {data.favorites} favorites"
            if is_html:
                result = f"<blockquote><b>Score:</b> {vote_data}</blockquote>"
            else:
                result = f"> > **Score**: {vote_data}  \n>  \n"
        return result

    async def _get_desctiption(self, data: AniMangaData, is_html: bool = True) -> str:
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
                         .replace('<br>', '  \n>')}  \n>  \n"
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

    async def _get_other_titles(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get alternative titles
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: Other titles section
        """
        other_titles = f"{f'{data.title_ro}, ' if data.title_en else ''}{data.title_ja}"
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
                    duration = await self._get_duration(data.duration)
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
                        f"https://anilist.co/studio/{studio[1]}",
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

    async def _get_links(self, data: AniMangaData, is_html: bool = True) -> str:
        """
        Get external links for an entry
        :param data: AniMangaData
        :param is_html: True for HTML, False for Markdown
        :return: External links section
        """
        result = ""
        if data.links or data.trailer and data.trailer[0] == "youtube" and data.trailer[1]:
            links = ""
            text = "🎬 <b>TRAILER</b>" if is_html else "🎬 **TRAILER**"
            if data.trailer:
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
                    f"https://anilist.co/search/{media_type}/{genre.replace(' ', '%20')}",
                    genre,
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
                    f"https://anilist.co/search/{media_type}?genres={tag.replace(' ', '%20')}",
                    tag,
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
                    f"https://anilist.co/{base_url}/{rel[1].id}",
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
            for i in range(1, len(other)):
                al_title = other[i].title_en if other[i].title_en else other[i].title_ro
                al_link = await self._get_link(
                    f"https://anilist.co/{media_type}/{other[i].id}",
                    al_title,
                    is_html
                )
                mal_link = ""
                if other[i].id_mal:
                    mal_link = await self._get_link(
                        f"https://myanimelist.net/{media_type}/{other[i].id_mal}",
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

    async def _get_duration(self, time: int) -> str:
        """
        Convert minutes to human-readable format
        :param time: minutes
        :return: formatted time X h Y min / X h / X min
        """
        if time >= 60:
            hours = time // 60
            minutes = time % 60
            duration = f"{hours} h"
            if minutes:
                duration += f" {minutes} min"
        else:
            duration = f"{time} min"
        return duration

    def get_max_results(self) -> int:
        """
        Get maximum number of results to return.
        :return: maximum number of results
        """
        return self._get_max_value("max_results", 4)

    def get_max_relations(self) -> int:
        """
        Get maximum number of relations to return.
        :return: maximum number of relations
        """
        return self._get_max_value("max_relations", 4)

    def _get_max_value(self, name: str, default: int) -> int:
        """
        Returns maximum value defined in config for parameter of specified name
        :param name: name of config parameter
        :param default: default maximum value
        :return: value for parameter of specified name
        """
        try:
            max_val = int(self.config.get(name, default))
            max_val = max(1, max_val)
        except ValueError:
            self.log.error(f"Incorrect '{name}' config value. Setting default value of {default}.")
            max_val = default
        return max_val

    async def get_matrix_image_url(self, url: str) -> str:
        """
        Download image from external URL and upload it to Matrix
        :param url: external URL
        :return: matrix mxc URL
        """
        image_url = ""
        try:
            response = await self.http.get(url, headers=self.headers, raise_for_status=True)
            data = await response.read()
            content_type = response.content_type
            extension = mimetypes.guess_extension(content_type)
            image_url = await self.client.upload_media(
                data=data,
                mime_type=content_type,
                filename=f"image{extension}",
                size=len(data)
            )
        except ClientError as e:
            self.log.error(f"Downloading image - connection failed: {e}")
        except (ValueError, MatrixResponseError) as e:
            self.log.error(f"Uploading image to Matrix server: {e}")
        return image_url

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
