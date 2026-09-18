import asyncio
import unittest
from unittest.mock import AsyncMock

import aiohttp
from aiohttp import ClientError
from mautrix.api import HTTPAPI
from mautrix.errors.base import MatrixResponseError
from mautrix.types import TextMessageEventContent
from mautrix.util.logging import TraceLogger
from maubot.matrix import MaubotMatrixClient

from animanga.animanga import AniMangaBot
from animanga.resources.datastructures import AniMangaData, SearchResult
from animanga.resources.formatters import Formatter
from animanga.resources.parsers import Parser
from .base_test import TestAniMangaBot

class TestAniMangaMal(TestAniMangaBot):
    def dupa(self):
        pass

if __name__ == '__main__':
    unittest.main()
