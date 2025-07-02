import aiohttp
import mimetypes
from datetime import datetime
from maubot import Plugin, MessageEvent
from maubot.handlers import command
from mautrix.types import TextMessageEventContent, MessageType, Format
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from typing import Type, Any
from .resources import queries
from .resources.datastructures import SearchResult, AniMangaData, media_formats, statuses, relation_types, seasons, months


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("max_results")
        helper.copy("max_relations")
        helper.copy("max_tags")


class AniMangaBot(Plugin):
    url = "https://graphql.anilist.co"
    headers = {
        "User-Agent": "AniMangaBot/1.0.0"
    }

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

    @command.new(name="anime", help="Search for titles of anime on AniList", require_subcommand=False, arg_fallthrough=False)
    @command.argument("title", pass_raw=True, required=True)
    async def anime(self, evt: MessageEvent, title: str) -> None:
        await evt.mark_read()
        title = title.strip()
        if not title:
            await evt.reply("> **Usage:**  \n"
                            "> !anime <title>")
            return
        await self.al_message_handler(evt, title, "ANIME")

    @command.new(name="manga", help="Search for titles of manga on AniList", require_subcommand=False, arg_fallthrough=False)
    @command.argument("title", pass_raw=True, required=True)
    async def manga(self, evt: MessageEvent, title: str) -> None:
        await evt.mark_read()
        title = title.strip()
        if not title:
            await evt.reply("> **Usage:**  \n"
                            "> !manga <title>")
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
            results_json = await self.al_get_results(json)
        except Exception as e:
            await evt.reply(f"> {e}")
            return
        # Parse results
        results = await self.al_parse_results(results_json)
        if not results:
            await evt.reply(f"Failed to find results for *{title}*")
            return

        # Get detailed information about the first entry from previous query
        query = queries.anime if media_type == "ANIME" else queries.manga
        try:
            json = {
                "query": query,
                "variables": {
                    "id": results[0].id
                }
            }
            main_result_json = await self.al_get_results(json)
        except Exception as e:
            await evt.reply(f"> {e}")
            return
        # Parse the detailed result
        main_result = await self.al_parse_main_result(main_result_json)
        if not main_result:
            await evt.reply(f"I've run into an internal problem while I was fetching results for *{title}*")
            return
        # Get the thumbnail
        if main_result.image:
            main_result.image = await self.get_matrix_image_url(main_result.image)

        # Prepare and send message
        content = await self.prepare_message(main_result, results)
        if content:
            await evt.reply(content)
        else:
            await evt.reply("Something went wrong when I was preparing the summary.")

    async def al_get_results(self, json: Any) -> Any:
        """
        Hit AniList API to get the results.
        :param json: structure containing the query and variables for the query
        :return: AniList API response
        """
        timeout = aiohttp.ClientTimeout(total=20)
        try:
            response = await self.http.post(self.url, json=json, headers=self.headers, timeout=timeout, raise_for_status=True)
            return await response.json()
        except aiohttp.ClientError as e:
            self.log.error(f"Connection to AniList API failed: {e}")
            raise Exception("Connection to AniList API failed.") from e

    async def al_parse_results(self, data: Any) -> list[SearchResult]:
        """
        Parse the initial results from AniList API
        :param data: AniList API response
        :return: list of search results
        """
        if data.get("errors", None):
            self.log.error(f"Error parsing results: {'; '.join([error.get('message', '') for error in data['errors']])}")
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

    async def al_parse_main_result(self, data: Any) -> AniMangaData | None:
        """
        Parse the main result from AniList API
        :param data: AniList API response
        :return: AniMangaData object or None if there are errors
        """
        if data.get("errors", None):
            self.log.error(f"Error parsing results: {'; '.join([error.get('message', '') for error in data['errors']])}")
            return None
        data = data["data"]["Media"]
        # Sort relations types in order defined in relation_types dictionary.
        # The default tuple for nonexistent relationType uses dict length in order to put it at the end of the list
        relations = [(relation_types.get(relation["relationType"], [relation["relationType"].title()])[0], SearchResult(
                id=relation["node"]["id"],
                id_mal=relation["node"]["idMal"],
                title_en=relation["node"]["title"].get("english", ""),
                title_ro=relation["node"]["title"].get("romaji", ""),
                media_type=relation["node"]["type"],
            )) for relation in sorted(data["relations"]["edges"], key=lambda rel: relation_types.get(rel["relationType"], ("", len(relation_types)))[1])]
        # Remove the so-called "Notes" section in the description because it makes the summary unnecessarily long
        description = ""
        if data["description"]:
            description_split = "Notes:" if "Notes:" in data["description"] else "Note:"
            description = data["description"].split(description_split)[0]
        result = AniMangaData(
            id=data["id"],
            id_mal=data["idMal"],
            title_ro=data["title"].get("romaji", ""),
            title_en=data["title"].get("english", ""),
            title_ja=data["title"].get("native", ""),
            type=data["type"],
            image=data["coverImage"].get("large", ""),
            # Date format: Apr 1, 2137
            start_date=(
                f"{months.get(data['startDate']['month']) + ' ' if data['startDate']['month'] else ''}"
                f"{str(data['startDate']['day']) + ', ' if data['startDate']['day'] else ''}"
                f"{data['startDate']['year'] if data['startDate']['year'] else ''}"
            ),
            end_date=(
                f"{months.get(data['endDate']['month']) + ' ' if data['endDate']['month'] else ''}"
                f"{str(data['endDate']['day']) + ', ' if data['endDate']['day'] else ''}"
                f"{data['endDate']['year'] if data['endDate']['year'] else ''}"
            ),
            description=description,
            average_score=data["averageScore"],
            mean_score=data["meanScore"],
            # Number of votes is the sum of votes for each score. API doesn't provide the total value
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
            next_episode_date = None
            if data["nextAiringEpisode"] and data["nextAiringEpisode"].get("airingAt", 0):
                next_episode_date = datetime.fromtimestamp(data["nextAiringEpisode"]["airingAt"]).strftime("%b %-d, %Y %H:%M")
            result.episodes = data["episodes"]
            result.season = seasons.get(data["season"], data["season"])
            result.season_year = data["seasonYear"]
            result.next_episode_num = data["nextAiringEpisode"].get("episode", 0) if data["nextAiringEpisode"] else None
            result.next_episode_date = next_episode_date
            result.duration = data["duration"]
            # Only include animation studios. AniList groups animation studios with producers here
            result.studios = [(studio["name"], studio["id"]) for studio in data["studios"]["nodes"] if studio["isAnimationStudio"]]
            # Get the number of producers
            result.studio_number = len(data["studios"]["nodes"]) - len(result.studios) if result.studios else 0
            result.trailer = (data["trailer"].get("site", ""), data["trailer"].get("id", "")) if data["trailer"] else ()
            result.volumes = 0
            result.chapters = 0
        else:
            result.episodes = 0
            result.season = ""
            result.season_year = 0
            result.next_episode_num = 0
            result.next_episode_date = ""
            result.duration = 0
            result.studios = []
            result.studio_number = 0
            result.trailer = ()
            result.volumes = data["volumes"]
            result.chapters = data["chapters"]
        return result

    async def prepare_message(self, data: AniMangaData, other: list[SearchResult]) -> TextMessageEventContent:
        """
        Prepare the final message based on the parsed results from AniList API
        :param data: AniMangaData object
        :param other: list of initial search results
        :return: text message for the user
        """
        media_type = data.type.lower() if data.type else "anime"
        # Title and description - panel 1
        title = data.title_en if data.title_en else data.title_ro
        body = f"> ### [{title}](https://anilist.co/{media_type}/{data.id})"
        html = (
            "<blockquote><table><tr><td>"
            f"<h3><a href=\"https://anilist.co/{media_type}/{data.id}\">{title}</a>"
        )
        if data.id_mal:
            body += f" ([MAL](https://myanimelist.net/{media_type}/{data.id_mal}))"
            html += f" <sup>(<a href=\"https://myanimelist.net/{media_type}/{data.id_mal}\">MAL</a>)</sup>"
        if data.nsfw:
            body += " 🔞"
            html += " 🔞"
        html += f"</h3>"

        # Description
        if data.description:
            body += f"  \n>  \n>{data.description.replace('\r', '').replace('\n', '').replace('<br>', '  \n>')}"
            html += f"<p>{data.description}</p>"

        body += "  \n>  \n"
        html += "</td><td>"
        # Image - panel 2
        if data.image:
            html += f"<img src=\"{data.image}\" height=\"200\" />"

        # Panel 3
        # Other titles
        other_titles = f"{f'{data.title_ro}, ' if data.title_en else ''}{data.title_ja}"
        body += f"> > **Other titles:** {other_titles}  \n>  \n"
        html += (
            "</td></tr><tr><td>"
            f"<blockquote><b>Other titles:</b> {other_titles}</blockquote>"
        )

        # Score
        score = None
        if data.average_score:
            score = float(data.average_score)/10
        elif data.mean_score:
            score = float(data.mean_score)/10
        if score:
            vote_data = f"⭐ {score}/10"
            if data.votes:
                vote_data += f" | 👤 {data.votes} votes"
            if data.favorites:
                vote_data += f" | ❤️ {data.favorites} favorites"
            body += f"> > **Score**: {vote_data}  \n>  \n"
            html += f"<blockquote><b>Score:</b> {vote_data}</blockquote>"

        # Format
        if data.format:
            media_format = data.format
            if data.episodes:
                media_format += f" | {data.episodes} episode{'s' if data.episodes > 1 else ''}"
                if data.duration:
                    if data.duration >= 60:
                        hours = data.duration // 60
                        minutes = data.duration % 60
                        duration = f"{hours} h"
                        if minutes:
                            duration += f" {minutes} min"
                    else:
                        duration = f"{data.duration} min"
                    media_format += f" ({duration}{' per episode' if data.episodes > 1 else ''})"
            if data.volumes:
                media_format += f" | {data.volumes} volumes"
            if data.chapters:
                media_format += f" | {data.chapters} chapters"
            body += f"> > **Format**: {media_format}  \n>  \n"
            html += f"<blockquote><b>Format:</b> {media_format}</blockquote>"

        # Status and next episode date
        broadcast = ""
        if data.next_episode_num and data.next_episode_date:
            broadcast = f" | Episode {data.next_episode_num} on {data.next_episode_date}"
        if data.status:
            body += f"> > **Status:** {data.status}{broadcast}  \n>  \n"
            html += f"<blockquote><b>Status:</b> {data.status}{broadcast}</blockquote>"

        # Dates, season
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
            body += f"> > **Released:** {released}  \n>  \n"
            html += f"<blockquote><b>Released:</b> {released}</blockquote>"

        # Studios
        if data.studios:
            body_studios = ", ".join([f"[{studio[0]}](https://anilist.co/studio/{studio[1]})" for studio in data.studios])
            html_studios = ", ".join([f"<a href=\"https://anilist.co/studio/{studio[1]}\">{studio[0]}</a>" for studio in data.studios])
            other_studios = f" + {data.studio_number} other{'s' if data.studio_number > 1 else ''}" if data.studio_number else ""
            body += f"> > **Studios:** {body_studios}{other_studios}  \n>  \n"
            html += f"<blockquote><b>Studios:</b> {html_studios}{other_studios}</blockquote>"

        # Links
        if data.links or data.trailer and data.trailer[0] == "youtube" and data.trailer[1]:
            body_links = ""
            html_links = ""
            if data.trailer:
                yt_link = f"https://www.youtube.com/watch?v={data.trailer[1]}"
                body_links += f"[🎬 **TRAILER**]({yt_link})"
                html_links += f"<a href=\"{yt_link}\">🎬 <b>TRAILER</b></a>"
            if data.links:
                body_links = body_links + ", " if body_links else body_links
                html_links = html_links + ", " if html_links else html_links
                body_links += ", ".join([f"[{link[0]}]({link[1]})" for link in data.links])
                html_links += ", ".join([f"<a href=\"{link[1]}\">{link[0]}</a>" for link in data.links])
            body += f"> > **Links:** {body_links}  \n>  \n"
            html += f"<blockquote><b>Links:</b> {html_links}</blockquote>"

        # Genres
        if data.genres:
            body_genres = ", ".join([f"[{genre}](https://anilist.co/search/{media_type}/{genre.replace(' ', '%20')})" for genre in data.genres])
            html_genres = ", ".join([f"<a href=\"https://anilist.co/search/{media_type}/{genre}\">{genre}</a>" for genre in data.genres])
            body += f"> > **Genres:** {body_genres}  \n>  \n"
            html += f"<blockquote><b>Genres:</b> {html_genres}</blockquote>"

        # Tags
        if data.tags:
            body_tags = ", ".join([f"[{tag}](https://anilist.co/search/{media_type}?genres={tag.replace(' ', '%20')})" for tag in data.tags])
            html_tags = ", ".join([f"<a href=\"https://anilist.co/search/{media_type}?genres={tag}\">{tag}</a>" for tag in data.tags])
            body += f"> > **Tags:** {body_tags}  \n>  \n"
            if len(data.tags) > self.get_max_tags():
                html += f"<blockquote><details><summary><b>Tags:</b></summary> {html_tags}</details></blockquote>"
            else:
                html += f"<blockquote><b>Tags:</b> {html_tags}</blockquote>"

        html += "</td><td><p>"
        # Relations - panel 4
        if data.relations:
            body += "> **Related entries:**  \n>  \n"
            html += "<b>Related entries:</b>"
            for i in range(0, len(data.relations)):
                rel = data.relations[i]
                base_url = rel[1].media_type.lower()
                al_title = rel[1].title_en if rel[1].title_en else rel[1].title_ro
                al_url = f"https://anilist.co/{base_url}/{rel[1].id}"
                body += f"> > {i + 1}. [{al_title}]({al_url})"
                html += f"<blockquote>[{rel[0]}]<br>{i + 1}. <a href=\"{al_url}\">{al_title}</a>"
                if rel[1].id_mal:
                    mal_url = f"https://myanimelist.net/{base_url}/{rel[1].id_mal}"
                    body += f" ([MAL]({mal_url}))"
                    html += f" <sup>(<a href=\"{mal_url}\">MAL</a>)</sup>"
                body += f" [{rel[0]}]  \n>  \n"
                html += f"</blockquote>"

        html += "</p></td></tr>"
        # Other results - panel 5
        if len(other) > 1:
            body += f"> **Other results:**  \n>  \n"
            html += "<tr><td><p><details><summary><b>Other results:</b></summary>"
            for i in range(1, len(other)):
                al_title = other[i].title_en if other[i].title_en else other[i].title_ro
                al_url = f"https://anilist.co/{media_type}/{other[i].id}"
                body += f"> > {i}. [{al_title}]({al_url})"
                html += f"<blockquote>{i}. <a href=\"{al_url}\">{al_title}</a>"
                if other[i].id_mal:
                    mal_url = f"https://myanimelist.net/{media_type}/{other[i].id_mal}"
                    body += f" ([MAL]({mal_url}))"
                    html += f" <sup>(<a href=\"{mal_url}\">MAL</a>)</sup>"
                body += "  \n>  \n"
                html += f"</blockquote>"
            html += "</details></p></td></tr>"

        body += "> **Results from AniList**"
        html += (
            "</table>"
            "<p><b><sub>Results from AniList</sub></b></p>"
            "</blockquote>"
        )

        return TextMessageEventContent(
                msgtype=MessageType.NOTICE,
                format=Format.HTML,
                body=body,
                formatted_body=html
            )

    def get_max_results(self) -> int:
        """
        Get maximum number of results to return.
        :return: maximum number of results
        """
        return self.get_max_value("max_results", 4)

    def get_max_relations(self) -> int:
        """
        Get maximum number of relations to return.
        :return: maximum number of relations
        """
        return self.get_max_value("max_relations", 4)

    def get_max_tags(self) -> int:
        """
        Get maximum number of tags before hiding them in dropdown.
        :return: maximum number of tags
        """
        return self.get_max_value("max_tags", 10)

    def get_max_value(self, name: str, default: int) -> int:
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
                size=len(data))
        except aiohttp.ClientError as e:
            self.log.error(f"Preparing image - connection failed: {url}: {e}")
        except Exception as e:
            self.log.error(f"Preparing image - unknown error: {url}: {e}")
        return image_url

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
