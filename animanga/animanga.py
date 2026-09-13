import io
import mimetypes
from typing import Any, Tuple, Type

from PIL import Image, UnidentifiedImageError
from aiohttp import ClientTimeout, ClientError
from mautrix.errors import MatrixResponseError
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command

from .resources import queries
from .resources.parsers import Parser
from .resources.formatters import Formatter


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("max_results")
        helper.copy("max_relations")
        helper.copy("use_mal_api")


class AniMangaBot(Plugin):
    al_url = "https://graphql.anilist.co"
    mal_url = "https://api.tenrai.org/v1"
    headers = {
        "User-Agent": "AniMangaBot/2.0.0"
    }
    pr = None
    fmt = None

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()
        self.pr = Parser(self.config, self.log)
        self.fmt = Formatter(self.config)

    @command.new(
        name="anime",
        help="Search for titles of anime on AniList / MyAnimeList",
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
        if self.config["use_mal_api"]:
            await self._mal_message_handler(evt, title, "ANIME")
        else:
            await self._al_message_handler(evt, title, "ANIME")

    @command.new(
        name="manga",
        help="Search for titles of manga on AniList / MyAnimeList",
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
        if self.config["use_mal_api"]:
            await self._mal_message_handler(evt, title, "MANGA")
        else:
            await self._al_message_handler(evt, title, "MANGA")

    async def _al_message_handler(self, evt: MessageEvent, title: str, media_type: str) -> None:
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
                    "perPage": self._get_max_results(),
                    "type": media_type,
                }
            }
            results_json = await self._al_get_results(json)
        except ClientError as e:
            await evt.reply(f"> {e}")
            return

        results = await self.pr.al_parse_results(results_json)
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

        main_result = await self.pr.al_parse_main_result(main_result_json)
        if not main_result:
            await evt.reply(
                f"> There happened to be a problem while fetching results for **{title}**"
            )
            return

        if main_result.image:
            main_result.image = await self._get_matrix_image_url(main_result.image)

        content = await self.fmt.prepare_message(main_result, results)
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
                self.al_url,
                json=json,
                headers=self.headers,
                timeout=timeout,
                raise_for_status=True
            )
            return await response.json()
        except ClientError as e:
            self.log.error(f"Connection to AniList API failed: {e}")
            raise ClientError("Connection to AniList API failed.") from e

    async def _mal_message_handler(self, evt: MessageEvent, title: str, media_type: str) -> None:
        """
        Commands the process of creating message for the user
        :param evt: user's message event
        :param title: anime or manga title
        :param media_type: type of medium
        """
        # Search for entries by title
        try:
            params = {
                "q": title,
                "limit": str(self._get_max_results()),
                "order_by": "popularity"
            }
            results_json = await self._mal_get_results(params, media_type.lower())
        except ClientError as e:
            await evt.reply(f"> {e}")
            return

        results = await self.pr.mal_parse_results(results_json)
        if not results:
            await evt.reply(f"Failed to find results for *{title}*")
            return

        # Get detailed information about the first entry from the previous query
        try:
            main_result_json = await self._mal_get_main_result(results[0].id, media_type)
        except ClientError as e:
            await evt.reply(f"> {e}")
            return

        main_result = await self.pr.mal_parse_main_result(main_result_json)
        if not main_result:
            await evt.reply(
                f"> There happened to be a problem while fetching results for **{title}**"
            )
            return

        if main_result.image:
            main_result.image = await self._get_matrix_image_url(main_result.image)

        content = await self.fmt.prepare_message(main_result, results)
        if content:
            await evt.reply(content)
        else:
            await evt.reply("> There happened to be a problem while preparing the summary.")

    async def _mal_get_results(self, params: Any, media_type: str) -> Any:
        """
        Hit Tenrai API to get the results.
        :param json: params for the query
        :return: Tenrai API response
        """
        timeout = ClientTimeout(total=20)
        try:
            response = await self.http.get(
                f"{self.mal_url}/{media_type}",
                params=params,
                headers=self.headers,
                timeout=timeout,
                raise_for_status=True
            )
            return await response.json()
        except ClientError as e:
            self.log.error(f"Connection to Tenrai API failed: {e}")
            raise ClientError("Connection to Tenrai API failed.") from e

    async def _mal_get_main_result(self, mal_id: int, media_type: str) -> Any:
        """
        Hit Tenrai API to get the results.
        :param json: params for the query
        :return: Tenrai API response
        """
        timeout = ClientTimeout(total=20)
        try:
            response = await self.http.get(
                f"{self.mal_url}/{media_type.lower()}/{mal_id}/full",
                headers=self.headers,
                timeout=timeout,
                raise_for_status=True
            )
            return await response.json()
        except ClientError as e:
            self.log.error(f"Connection to Tenrai API failed: {e}")
            raise ClientError("Connection to Tenrai API failed.") from e

    def _get_max_results(self) -> int:
        """
        Get maximum number of results to return.
        :return: maximum number of results
        """
        return self.pr.get_max_value("max_results", 4)

    async def _get_matrix_image_url(self, url: str) -> str:
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
            self.fmt.width, self.fmt.height = await self.loop.run_in_executor(
                None,
                self._get_image_dimensions,
                data
            )
        except ClientError as e:
            self.log.error(f"Downloading image - connection failed: {e}")
        except (ValueError, MatrixResponseError) as e:
            self.log.error(f"Uploading image to Matrix server: {e}")
        return image_url

    def _get_image_dimensions(self, image: bytes) -> Tuple[int, int]:
        """
        Examine image dimensions
        :param image: image data as bytes
        :return: Tuple with image width and height
        """
        try:
            img = Image.open(io.BytesIO(image))
            return img.width, img.height
        except (ValueError, TypeError, FileNotFoundError, UnidentifiedImageError) as e:
            self.log.error(f"Error reading image dimensions: {e}")
            return 230, 325

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
