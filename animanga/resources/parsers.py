from datetime import datetime
from typing import Any, Tuple

from mautrix.util.config import BaseProxyConfig
from mautrix.util.logging import TraceLogger

from .datastructures import (
    SearchResult,
    AniMangaData,
    media_formats,
    statuses,
    relation_types,
    seasons,
    months
)


class Parser:
    def __init__(self, config: BaseProxyConfig | None, log: TraceLogger) -> None:
        self.config = config
        self.log = log

    async def al_parse_results(self, data: Any) -> list[SearchResult]:
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

    async def al_parse_main_result(self, data: Any) -> AniMangaData | None:
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
        relations = await self._al_parse_relations(data["relations"]["edges"])
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
            description=await self._parse_description(data),
            average_score=data["averageScore"] * 10 if data["averageScore"] else 0,
            mean_score=data["meanScore"] * 10 if data["meanScore"] else 0,
            votes=await self._parse_votes(data),
            favorites=data["favourites"],
            nsfw=data["isAdult"],
            format=media_formats.get(data["format"], data["format"]),
            status=statuses.get(data["status"], data["status"]),
            genres=[(genre, 0) for genre in data["genres"]],
            # Do not include tags that are marked as spoilers
            tags=[(tag["name"], 0) for tag in data["tags"] if not tag["isMediaSpoiler"]],
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
                if data["nextAiringEpisode"] else 0
            )
            result.next_episode_date = await self._parse_next_airing_episode(data)
            result.duration = await self._al_parse_duration(data["duration"])
            result.studios = studios
            result.studio_number = studio_number
            result.trailer = (
                (data["trailer"].get("site", ""), data["trailer"].get("id", ""))
                if data["trailer"] else ()
            )
            result.volumes = 0
            result.chapters = 0
            result.authors = []
        else:
            result.episodes = 0
            result.season = ""
            result.season_year = 0
            result.next_episode_num = 0
            result.next_episode_date = ""
            result.duration = ""
            result.studios = set()
            result.studio_number = 0
            result.trailer = ()
            result.volumes = data["volumes"]
            result.chapters = data["chapters"]
            result.authors = await self._parse_authors(data["staff"]["edges"])
        return result

    async def mal_parse_results(self, data: Any) -> list[SearchResult]:
        """
        Parse the initial results from Tenrai API
        :param data: Tenrai API response
        :return: list of search results
        """
        if data.get("error", None):
            self.log.error(f"Error parsing results: {data["message"]}")
            return []
        results: list[SearchResult] = []
        for result in data["data"]:
            sr = SearchResult(
                id=result["mal_id"],
                id_mal=0,
                title_ro=result["title"],
                title_en=result["title_english"],
            )
            results.append(sr)
        return results

    async def mal_parse_main_result(self, data: Any) -> AniMangaData | None:
        """
        Parse the main result from Tenrai API
        :param data: Tenrai API response
        :return: AniMangaData object or None if there are errors
        """
        if data.get("error", None):
            self.log.error(f"Error parsing results: {data["message"]}")
            return None
        data = data["data"]
        relations = await self._mal_parse_relations(data["relations"])

        result = AniMangaData(
            id=data["mal_id"],
            id_mal=0,
            title_ro=data["title"],
            title_en=data["title_english"],
            title_ja=data["title_japanese"],
            type="ANIME" if data["url"].startswith("https://myanimelist.net/anime") else "MANGA",
            image=data["images"]["webp"]["image_url"],
            description=data["synopsis"],
            average_score=data["score"] * 100 if data["score"] else 0,
            mean_score=data["score"] * 100 if data["score"] else 0,
            votes=data["scored_by"],
            favorites=data["favorites"],
            nsfw=False,
            format=data["type"],
            status=data["status"],
            genres=[(genre["name"], genre["mal_id"]) for genre in data["genres"]] +
                   [(genre["name"], genre["mal_id"]) for genre in data["explicit_genres"]],
            tags=[(tag["name"], tag["mal_id"]) for tag in data["themes"]] +
                 [(tag["name"], tag["mal_id"]) for tag in data["demographics"]],
            relations=relations[:self.get_max_relations()],
            links=[(link["name"], link["url"]) for link in data["external"]] +
                  [(link["name"], link["url"]) for link in data.get("streaming", [])],
        )
        if result.type == "ANIME":
            result.episodes = data["episodes"]
            result.season = data["season"].title() if data["season"] else ""
            result.season_year = data["year"]
            result.next_episode_num = 0
            result.next_episode_date = data["broadcast"]["string"]
            result.duration = await self._mal_parse_duration(data["duration"])
            result.studios = {(st["name"], st["mal_id"]) for st in data["studios"]}
            result.studio_number = len(data["producers"]) + len(data["licensors"])
            result.trailer = (
                ("youtube", data["trailer"].get("youtube_id", ""))
                if data["trailer"] else ()
            )
            result.volumes = 0
            result.chapters = 0
            result.authors = []
            result.start_date = await self._parse_date(data["aired"]["prop"], "from")
            result.end_date = await self._parse_date(data["aired"]["prop"], "to")
        else:
            result.episodes = 0
            result.season = ""
            result.season_year = 0
            result.next_episode_num = 0
            result.next_episode_date = ""
            result.duration = ""
            result.studios = set()
            result.studio_number = 0
            result.trailer = ()
            result.volumes = data["volumes"]
            result.chapters = data["chapters"]
            result.authors = [
                (author["name"], author["role"], author["mal_id"])
                for author in data["authors"]
            ]
            result.start_date = await self._parse_date(data["published"]["prop"], "from")
            result.end_date = await self._parse_date(data["published"]["prop"], "to")
        return result

    async def _mal_parse_duration(self, duration: str) -> str:
        if not duration or duration == "Unknown":
            return ""
        return duration.rstrip("per ep")

    async def _mal_parse_relations(self, relations_raw: Any) -> list[tuple[Any, SearchResult]]:
        """
        Sort relation types in order defined in relation_types dictionary.
        :param relations_raw: raw list od relations from API
        :return: sorted list of relations
        """
        relations = []
        for relation in relations_raw:
            for entry in relation["entry"]:
                rel = (
                    relation["relation"],
                    SearchResult(
                        id=entry["mal_id"],
                        id_mal=0,
                        title_en="",
                        title_ro=entry["name"],
                        media_type=entry["type"].upper(),
                    )
                )
                relations.append(rel)
        return relations

    async def _al_parse_relations(self, relations_raw: Any) -> list[tuple[Any, SearchResult]]:
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

    async def _parse_description(self, data: Any) -> str:
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
        return description.rstrip().removesuffix("<i>")

    async def _parse_votes(self, data: Any) -> int:
        """
        Get the number of votes. It is the sum of votes of each score.
        API doesn't provide the total value
        :param data: JSON data from API
        :return: number of votes
        """
        if data["stats"]["scoreDistribution"] is None:
            return 0
        return sum(score["amount"] for score in data["stats"]["scoreDistribution"])

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

    async def _parse_next_airing_episode(self, data: Any) -> str:
        """
        Get date and time for the next airing episode
        :param data: JSON data from API
        :return: formatted date
        """
        next_episode_date = ""
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

    async def _parse_authors(self, authors_raw: Any) -> list[Tuple[str, str, int]]:
        authors: list[Tuple[str, str, int]] = []
        allowed_roles = ["Story", "Art", "Story & Art", "Original Story", "Original Creator"]
        for author in authors_raw:
            if author["role"] in allowed_roles:
                authors.append(
                    (author["node"]["name"]["full"], author["role"], author["node"]["id"])
                )
        return authors

    async def _al_parse_duration(self, time: int) -> str:
        """
        Convert minutes to human-readable format
        :param time: minutes
        :return: formatted time X h Y min / X h / X min
        """
        if not time:
            return ""
        if time >= 60:
            hours = time // 60
            minutes = time % 60
            duration = f"{hours} h"
            if minutes:
                duration += f" {minutes} min"
        else:
            duration = f"{time} min"
        return duration

    def get_max_relations(self) -> int:
        """
        Get maximum number of relations to return.
        :return: maximum number of relations
        """
        return self.get_max_value("max_relations", 4)

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
