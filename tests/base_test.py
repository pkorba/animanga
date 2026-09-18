import asyncio
import unittest
from unittest.mock import AsyncMock

import aiohttp
from mautrix.api import HTTPAPI
from mautrix.util.logging import TraceLogger
from maubot.matrix import MaubotMatrixClient

from animanga.animanga import AniMangaBot
from animanga.resources.formatters import Formatter
from animanga.resources.parsers import Parser


class TestAniMangaBot(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = aiohttp.ClientSession()
        api = HTTPAPI(base_url="http://matrix.example.com", client_session=self.session)
        client = MaubotMatrixClient(api=api)
        self.bot = AniMangaBot(
            client=client,
            loop=asyncio.get_event_loop(),
            http=self.session,
            instance_id="matrix.example.com",
            log=TraceLogger("testlogger"),
            config=None,
            database=None,
            webapp=None,
            webapp_url=None,
            loader=None
        )
        pr = Parser(self.bot.config, self.bot.log)
        fmt = Formatter(self.bot.config)
        self.bot.pr = pr
        self.bot.fmt = fmt

    async def asyncTearDown(self):
        await self.session.close()

    async def create_resp(
            self,
            status_code=200,
            json=None,
            resp_bytes=None,
            content_type=None,
            content_length=0
    ):
        resp = AsyncMock(
            status_code=status_code,
            content_type=content_type,
            content_length=content_length
        )
        resp.json.return_value = json
        resp.read.return_value = resp_bytes
        return resp

if __name__ == '__main__':
    unittest.main()
