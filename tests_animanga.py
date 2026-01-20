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
from .animanga.resources.datastructures import AniMangaData, SearchResult


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

    async def test_get_duration(self):
        # Arrange
        config = (
            (0, "0 min"),
            (59, "59 min"),
            (60, "1 h"),
            (61, "1 h 1 min"),
            (120, "2 h"),
            (150, "2 h 30 min"),
        )
        for minutes, expected_result in config:
            with self.subTest(minutes=minutes, expected_result=expected_result):
                # Act
                result = await self.bot._get_duration(minutes)

                # Assert
                self.assertEqual(result, expected_result)

    async def test_get_max_value(self):
        # Arrange
        config = (
            ({"test": 0}, 1),
            ({"test": -2}, 1),
            ({"test": 2}, 2),
            ({"ttest": 2}, 5),
            ({"test": "2"}, 2),
            ({"test": 2.0}, 2),
        )
        for config_dict, expected_result in config:
            with self.subTest(config_dict=config_dict, expected_result=expected_result):
                self.bot.config = config_dict

                # Act
                result = self.bot._get_max_value("test", 5)

                # Assert
                self.assertEqual(result, expected_result)

    async def test_al_get_results_when_request_is_successful_then_return_json(self):
        # Arrange
        json_data = {"test": 1}
        self.bot.http.post = AsyncMock(return_value=await self.create_resp(200, json=json_data))

        # Act
        json_response = await self.bot._al_get_results({"json": "test"})

        # Assert
        self.assertEqual(json_response, json_data)

    async def test_al_get_results_when__aiohttp_error_then_raise_exception(self):
        # Arrange
        self.bot.http.post = AsyncMock(side_effect=ClientError)

        # Assert
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            with self.assertRaisesRegex(ClientError, "Connection to AniList API failed."):
                # Act
                await self.bot._al_get_results({"json": "test"})
            self.assertEqual(['ERROR:testlogger:Connection to AniList API failed: '], logger.output)

    async def test_al_parse_results_when_correct_data_return_list_of_SearchResult(self):
        # Arrange
        data = {
            "data": {
                "Page": {
                    "media": [
                        {
                            "id": 16498,
                            "idMal": 16498,
                            "title": {
                                "romaji": "Shingeki no Kyojin",
                                "english": "Attack on Titan"
                            }
                        },
                        {
                            "id": 18397,
                            "idMal": 18397,
                            "title": {
                                "romaji": "Shingeki no Kyojin OVA",
                                "english": None
                            }
                        },
                        {
                            "id": 110277,
                            "idMal": 40028,
                            "title": {
                                "romaji": "Shingeki no Kyojin: The Final Season",
                                "english": "Attack on Titan Final Season"
                            }
                        }
                    ]
                }
            }
        }

        expected_results = [
            SearchResult(
                id=16498,
                id_mal=16498,
                title_en="Attack on Titan",
                title_ro="Shingeki no Kyojin",
            ),
            SearchResult(
                id=18397,
                id_mal=18397,
                title_en=None,
                title_ro="Shingeki no Kyojin OVA",
            ),
            SearchResult(
                id=110277,
                id_mal=40028,
                title_en="Attack on Titan Final Season",
                title_ro="Shingeki no Kyojin: The Final Season",
            )
        ]

        # Act
        results = await self.bot._al_parse_results(data)

        # Assert
        self.assertIsInstance(results[0], SearchResult)
        self.assertEqual(results, expected_results)

    async def test_al_parse_results_when_error_return_empty_list(self):
        # Arrange
        data = {
            "errors": [
                {
                    "message": "Error message",
                    "status": 400,
                    "locations": [
                        {
                            "line": 7,
                            "column": 17
                        }
                    ]
                },
                {
                    "message": "Error message 2",
                    "status": 400,
                    "locations": [
                        {
                            "line": 27,
                            "column": 37
                        }
                    ]
                }
            ],
            "data": None
        }

        # Act
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            results = await self.bot._al_parse_results(data)

            # Assert
            self.assertEqual(
                ["ERROR:testlogger:Error parsing results: Error message; Error message 2"],
                logger.output
            )
            self.assertEqual(results, [])

    async def test_al_parse_main_result_when_correct_anime_data_return_AniMangaData(self):
        # Arrange
        self.bot.config = {}
        data = {
            "data": {
                "Media": {
                    "id": 171018,
                    "idMal": 57334,
                    "title": {
                        "romaji": "Romaji",
                        "english": "English",
                        "native": "Native"
                    },
                    "type": "ANIME",
                    "coverImage": {
                        "large": "https://anilist.example.com/media/anime/cover/medium/12345.jpg"
                    },
                    "trailer": {
                        "site": "youtube",
                        "id": "qwertyuiopa"
                    },
                    "startDate": {
                        "day": 4,
                        "month": 10,
                        "year": 2024
                    },
                    "endDate": {
                        "day": 20,
                        "month": 12,
                        "year": 2024
                    },
                    "description": (
                        "Desctiption!<br><br>\n(Source: Crunchyroll) "
                        "<br><br>\n\nNotes: <br>\n- Some notes"
                    ),
                    "averageScore": 84,
                    "meanScore": 85,
                    "stats": {
                        "scoreDistribution": [
                            {
                                "amount": 569
                            },
                            {
                                "amount": 155
                            },
                            {
                                "amount": 353
                            },
                            {
                                "amount": 501
                            },
                            {
                                "amount": 1523
                            },
                            {
                                "amount": 2657
                            },
                            {
                                "amount": 10408
                            },
                            {
                                "amount": 29199
                            },
                            {
                                "amount": 44961
                            },
                            {
                                "amount": 23086
                            }
                        ]
                    },
                    "favourites": 15063,
                    "isAdult": True,
                    "format": "TV",
                    "status": "FINISHED",
                    "genres": [
                        "Action",
                        "Comedy",
                        "Drama",
                        "Romance",
                        "Sci-Fi",
                        "Supernatural"
                    ],
                    "tags": [
                        {
                            "name": "Urban Fantasy",
                            "isMediaSpoiler": False
                        },
                        {
                            "name": "Youkai",
                            "isMediaSpoiler": False
                        },
                        {
                            "name": "Ghost",
                            "isMediaSpoiler": False
                        },
                        {
                            "name": "Suicide",
                            "isMediaSpoiler": True
                        }
                    ],
                    "episodes": 12,
                    "season": "FALL",
                    "seasonYear": 2024,
                    "nextAiringEpisode": {
                        "airingAt": 1756652400,
                        "episode": 9
                    },
                    "duration": 24,
                    "relations": {
                        "edges": [
                            {
                                "relationType": "ADAPTATION",
                                "node": {
                                    "id": 132029,
                                    "idMal": 135496,
                                    "title": {
                                        "romaji": "Adaptation Romaji",
                                        "english": "Adaptation English"
                                    },
                                    "type": "MANGA"
                                }
                            },
                            {
                                "relationType": "CHARACTER",
                                "node": {
                                    "id": 185586,
                                    "idMal": 60461,
                                    "title": {
                                        "romaji": "Character Romaji",
                                        "english": "Character English"
                                    },
                                    "type": "ANIME"
                                }
                            },
                            {
                                "relationType": "SEQUEL",
                                "node": {
                                    "id": 185660,
                                    "idMal": 60543,
                                    "title": {
                                        "romaji": "Sequel Romaji",
                                        "english": "Sequel English"
                                    },
                                    "type": "ANIME"
                                }
                            }
                        ]
                    },
                    "studios": {
                        "edges": [
                            {
                                "isMain": True,
                                "node": {
                                    "id": 6145,
                                    "name": "Studio 1"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 143,
                                    "name": "Studio 2"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 6145,
                                    "name": "Studio 1"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 6570,
                                    "name": "Studio 3"
                                }
                            },
                            {
                                "isMain": True,
                                "node": {
                                    "id": 53,
                                    "name": "Studio 4"
                                }
                            }
                        ]
                    },
                    "externalLinks": [
                        {
                            "url": "https://twitter.example.com/anime_title",
                            "site": "Twitter"
                        },
                        {
                            "url": "https://example.com/",
                            "site": "Official Site"
                        }
                    ]
                }
            }
        }
        relations = [
            (
                'Adaptation',
                SearchResult(
                    id=132029,
                    id_mal=135496,
                    title_en='Adaptation English',
                    title_ro='Adaptation Romaji',
                    media_type='MANGA')
            ),
            (
                'Sequel',
                SearchResult(
                    id=185660,
                    id_mal=60543,
                    title_en='Sequel English',
                    title_ro='Sequel Romaji',
                    media_type='ANIME')
            ),
            (
                'Character',
                SearchResult(
                    id=185586,
                    id_mal=60461,
                    title_en='Character English',
                    title_ro='Character Romaji',
                    media_type='ANIME')
            )]

        # Act
        result = await self.bot._al_parse_main_result(data)

        # Assert
        self.assertIsInstance(result, AniMangaData)
        self.assertEqual(result.id, 171018)
        self.assertEqual(result.id_mal, 57334)
        self.assertEqual(result.title_ro, "Romaji")
        self.assertEqual(result.title_en, "English")
        self.assertEqual(result.title_ja, "Native")
        self.assertEqual(result.type, "ANIME")
        self.assertEqual(
            result.image,
            "https://anilist.example.com/media/anime/cover/medium/12345.jpg"
        )
        self.assertEqual(result.start_date, "4 Oct 2024")
        self.assertEqual(result.end_date, "20 Dec 2024")
        self.assertEqual(
            result.description,
            "Desctiption!<br><br>\n(Source: Crunchyroll) <br><br>\n\n"
        )
        self.assertEqual(result.average_score, 84)
        self.assertEqual(result.mean_score, 85)
        self.assertEqual(result.votes, 113412)
        self.assertEqual(result.favorites, 15063)
        self.assertEqual(result.nsfw, True)
        self.assertEqual(result.format, "TV Show")
        self.assertEqual(result.status, "Finished")
        self.assertEqual(
            result.genres,
            ["Action", "Comedy", "Drama", "Romance", "Sci-Fi", "Supernatural"]
        )
        self.assertEqual(result.tags, ["Urban Fantasy", "Youkai", "Ghost"])
        self.assertEqual(result.relations, relations)
        self.assertEqual(
            result.links,
            [
                ("Twitter", "https://twitter.example.com/anime_title"),
                ("Official Site", "https://example.com/")
            ]
        )
        self.assertEqual(result.episodes, 12)
        self.assertEqual(result.season, "Fall")
        self.assertEqual(result.season_year, 2024)
        self.assertEqual(result.next_episode_num, 9)
        self.assertEqual(result.next_episode_date, "Sunday, 31 Aug 2025, 17:00")
        self.assertEqual(result.duration, 24)
        self.assertEqual(result.studios, {("Studio 1", 6145), ("Studio 4", 53)})
        self.assertEqual(result.studio_number, 3)
        self.assertEqual(result.trailer, ('youtube', 'qwertyuiopa'))
        self.assertEqual(result.volumes, 0)
        self.assertEqual(result.chapters, 0)

    async def test_al_parse_main_result_when_no_anime_data_return_empty_AniMangaData(self):
        # Arrange
        self.bot.config = {}
        data = {
            "data": {
                "Media": {
                    "id": 171018,
                    "idMal": None,
                    "title": {
                        "romaji": "Romaji",
                        "english": None,
                        "native": None
                    },
                    "type": "ANIME",
                    "coverImage": {
                        "large": None
                    },
                    "trailer": None,
                    "startDate": {
                        "day": None,
                        "month": None,
                        "year": None
                    },
                    "endDate": {
                        "day": None,
                        "month": None,
                        "year": None
                    },
                    "description": None,
                    "averageScore": None,
                    "meanScore": None,
                    "stats": {
                        "scoreDistribution": []
                    },
                    "favourites": None,
                    "isAdult": False,
                    "format": None,
                    "status": None,
                    "genres": [],
                    "tags": [],
                    "episodes": None,
                    "season": None,
                    "seasonYear": None,
                    "nextAiringEpisode": None,
                    "duration": None,
                    "relations": {
                        "edges": []
                    },
                    "studios": {
                        "edges": []
                    },
                    "externalLinks": []
                }
            }
        }

        # Act
        result = await self.bot._al_parse_main_result(data)

        # Assert
        self.assertIsInstance(result, AniMangaData)
        self.assertEqual(result.id, 171018)
        self.assertEqual(result.id_mal, None)
        self.assertEqual(result.title_ro, "Romaji")
        self.assertEqual(result.title_en, None)
        self.assertEqual(result.title_ja, None)
        self.assertEqual(result.type, "ANIME")
        self.assertEqual(result.image, None)
        self.assertEqual(result.start_date, "")
        self.assertEqual(result.end_date, "")
        self.assertEqual(result.description, "")
        self.assertEqual(result.average_score, None)
        self.assertEqual(result.mean_score, None)
        self.assertEqual(result.votes, 0)
        self.assertEqual(result.favorites, None)
        self.assertEqual(result.nsfw, False)
        self.assertEqual(result.format, None)
        self.assertEqual(result.status, None)
        self.assertEqual(result.genres, [])
        self.assertEqual(result.tags, [])
        self.assertEqual(result.relations, [])
        self.assertEqual(result.links, [])
        self.assertEqual(result.episodes, None)
        self.assertEqual(result.season, None)
        self.assertEqual(result.season_year, None)
        self.assertEqual(result.next_episode_num, None)
        self.assertEqual(result.next_episode_date, None)
        self.assertEqual(result.duration, None)
        self.assertEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ())
        self.assertEqual(result.volumes, 0)
        self.assertEqual(result.chapters, 0)

    async def test_al_parse_main_result_when_correct_manga_data_return_AniMangaData(self):
        # Arrange
        self.bot.config = {}
        data = {
            "data": {
                "Media": {
                    "id": 171018,
                    "idMal": 57334,
                    "title": {
                        "romaji": "Romaji",
                        "english": "English",
                        "native": "Native"
                    },
                    "type": "MANGA",
                    "coverImage": {
                        "large": "https://anilist.example.com/media/anime/cover/medium/12345.jpg"
                    },
                    "startDate": {
                        "day": 4,
                        "month": 10,
                        "year": 2024
                    },
                    "endDate": {
                        "day": 20,
                        "month": 12,
                        "year": 2024
                    },
                    "description": (
                        "Desctiption!<br><br>\n(Source: VIZ Media) "
                        "<br><br>\n\nNotes: <br>\n- Some notes"
                    ),
                    "averageScore": 84,
                    "meanScore": 85,
                    "stats": {
                        "scoreDistribution": [
                            {
                                "amount": 569
                            },
                            {
                                "amount": 155
                            },
                            {
                                "amount": 353
                            },
                            {
                                "amount": 501
                            },
                            {
                                "amount": 1523
                            },
                            {
                                "amount": 2657
                            },
                            {
                                "amount": 10408
                            },
                            {
                                "amount": 29199
                            },
                            {
                                "amount": 44961
                            },
                            {
                                "amount": 23086
                            }
                        ]
                    },
                    "volumes": 5,
                    "chapters": 100,
                    "favourites": 15063,
                    "isAdult": True,
                    "format": "MANGA",
                    "status": "FINISHED",
                    "genres": [
                        "Action",
                        "Comedy",
                        "Drama",
                        "Romance",
                        "Sci-Fi",
                        "Supernatural"
                    ],
                    "tags": [
                        {
                            "name": "Urban Fantasy",
                            "isMediaSpoiler": False
                        },
                        {
                            "name": "Youkai",
                            "isMediaSpoiler": False
                        },
                        {
                            "name": "Ghost",
                            "isMediaSpoiler": False
                        },
                        {
                            "name": "Suicide",
                            "isMediaSpoiler": True
                        }
                    ],
                    "relations": {
                        "edges": [
                            {
                                "relationType": "ADAPTATION",
                                "node": {
                                    "id": 132029,
                                    "idMal": 135496,
                                    "title": {
                                        "romaji": "Adaptation Romaji",
                                        "english": "Adaptation English"
                                    },
                                    "type": "ANIME"
                                }
                            },
                            {
                                "relationType": "CHARACTER",
                                "node": {
                                    "id": 185586,
                                    "idMal": 60461,
                                    "title": {
                                        "romaji": "Character Romaji",
                                        "english": "Character English"
                                    },
                                    "type": "ANIME"
                                }
                            },
                            {
                                "relationType": "SIDE_STORY",
                                "node": {
                                    "id": 185660,
                                    "idMal": 60543,
                                    "title": {
                                        "romaji": "Side Story Romaji",
                                        "english": "Side Story English"
                                    },
                                    "type": "MANGA"
                                }
                            }
                        ]
                    },
                    "externalLinks": [
                        {
                            "url": "https://twitter.example.com/anime_title",
                            "site": "Twitter"
                        },
                        {
                            "url": "https://example.com/",
                            "site": "Official Site"
                        }
                    ]
                }
            }
        }
        relations = [
            (
                'Adaptation',
                SearchResult(
                    id=132029,
                    id_mal=135496,
                    title_en='Adaptation English',
                    title_ro='Adaptation Romaji',
                    media_type='ANIME')
            ),
            (
                'Side Story',
                SearchResult(
                    id=185660,
                    id_mal=60543,
                    title_en='Side Story English',
                    title_ro='Side Story Romaji',
                    media_type='MANGA')
            ),
            (
                'Character',
                SearchResult(
                    id=185586,
                    id_mal=60461,
                    title_en='Character English',
                    title_ro='Character Romaji',
                    media_type='ANIME')
            )]

        # Act
        result = await self.bot._al_parse_main_result(data)

        # Assert
        self.assertIsInstance(result, AniMangaData)
        self.assertEqual(result.id, 171018)
        self.assertEqual(result.id_mal, 57334)
        self.assertEqual(result.title_ro, "Romaji")
        self.assertEqual(result.title_en, "English")
        self.assertEqual(result.title_ja, "Native")
        self.assertEqual(result.type, "MANGA")
        self.assertEqual(
            result.image,
            "https://anilist.example.com/media/anime/cover/medium/12345.jpg"
        )
        self.assertEqual(result.start_date, "4 Oct 2024")
        self.assertEqual(result.end_date, "20 Dec 2024")
        self.assertEqual(
            result.description,
            "Desctiption!<br><br>\n(Source: VIZ Media) <br><br>\n\n"
        )
        self.assertEqual(result.average_score, 84)
        self.assertEqual(result.mean_score, 85)
        self.assertEqual(result.votes, 113412)
        self.assertEqual(result.favorites, 15063)
        self.assertEqual(result.nsfw, True)
        self.assertEqual(result.format, "Manga")
        self.assertEqual(result.status, "Finished")
        self.assertEqual(
            result.genres,
            ["Action", "Comedy", "Drama", "Romance", "Sci-Fi", "Supernatural"]
        )
        self.assertEqual(result.tags, ["Urban Fantasy", "Youkai", "Ghost"])
        self.assertEqual(result.relations, relations)
        self.assertEqual(
            result.links,
            [
                ("Twitter", "https://twitter.example.com/anime_title"),
                ("Official Site", "https://example.com/")
            ]
        )
        self.assertEqual(result.episodes, 0)
        self.assertEqual(result.season, "")
        self.assertEqual(result.season_year, 0)
        self.assertEqual(result.next_episode_num, 0)
        self.assertEqual(result.next_episode_date, "")
        self.assertEqual(result.duration, 0)
        self.assertEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ())
        self.assertEqual(result.volumes, 5)
        self.assertEqual(result.chapters, 100)

    async def test_al_parse_main_result_when_no_manga_data_return_empty_AniMangaData(self):
        # Arrange
        self.bot.config = {}
        data = {
            "data": {
                "Media": {
                    "id": 163272,
                    "idMal": None,
                    "title": {
                        "romaji": "Romaji",
                        "english": None,
                        "native": None
                    },
                    "type": "MANGA",
                    "coverImage": {
                        "large": None
                    },
                    "startDate": {
                        "day": None,
                        "month": None,
                        "year": None
                    },
                    "endDate": {
                        "day": None,
                        "month": None,
                        "year": None
                    },
                    "description": None,
                    "averageScore": None,
                    "meanScore": None,
                    "stats": {
                        "scoreDistribution": []
                    },
                    "volumes": None,
                    "chapters": None,
                    "favourites": None,
                    "isAdult": False,
                    "format": None,
                    "status": None,
                    "genres": [],
                    "tags": [],
                    "relations": {
                        "edges": []
                    },
                    "externalLinks": []
                }
            }
        }

        # Act
        result = await self.bot._al_parse_main_result(data)

        # Assert
        self.assertIsInstance(result, AniMangaData)
        self.assertEqual(result.id, 163272)
        self.assertEqual(result.id_mal, None)
        self.assertEqual(result.title_ro, "Romaji")
        self.assertEqual(result.title_en, None)
        self.assertEqual(result.title_ja, None)
        self.assertEqual(result.type, "MANGA")
        self.assertEqual(result.image, None)
        self.assertEqual(result.start_date, "")
        self.assertEqual(result.end_date, "")
        self.assertEqual(result.description, "")
        self.assertEqual(result.average_score, None)
        self.assertEqual(result.mean_score, None)
        self.assertEqual(result.votes, 0)
        self.assertEqual(result.favorites, None)
        self.assertEqual(result.nsfw, False)
        self.assertEqual(result.format, None)
        self.assertEqual(result.status, None)
        self.assertEqual(result.genres, [])
        self.assertEqual(result.tags, [])
        self.assertEqual(result.relations, [])
        self.assertEqual(result.links, [])
        self.assertEqual(result.episodes, 0)
        self.assertEqual(result.season, "")
        self.assertEqual(result.season_year, 0)
        self.assertEqual(result.next_episode_num, 0)
        self.assertEqual(result.next_episode_date, "")
        self.assertEqual(result.duration, 0)
        self.assertEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ())
        self.assertEqual(result.volumes, None)
        self.assertEqual(result.chapters, None)

    async def test_al_parse_main_result_when_error_return_None(self):
        # Arrange
        data = {
            "errors": [
                {
                    "message": "Error message",
                    "status": 400,
                    "locations": [
                        {
                            "line": 7,
                            "column": 17
                        }
                    ]
                },
                {
                    "message": "Error message 2",
                    "status": 400,
                    "locations": [
                        {
                            "line": 27,
                            "column": 37
                        }
                    ]
                }
            ],
            "data": None
        }

        # Act
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            results = await self.bot._al_parse_main_result(data)

            # Assert
            self.assertEqual(
                ["ERROR:testlogger:Error parsing results: Error message; Error message 2"],
                logger.output
            )
            self.assertEqual(results, None)

    async def test_parse_relations(self):
        # Arrange
        data = (
            [
                {
                    "relationType": "ADAPTATION",
                    "node": {
                        "id": 132029,
                        "idMal": 135496,
                        "title": {
                            "romaji": "Adaptation Romaji",
                            "english": "Adaptation English"
                        },
                        "type": "MANGA"
                    }
                },
                {
                    "relationType": "CHARACTER",
                    "node": {
                        "id": 185586,
                        "idMal": 60461,
                        "title": {
                            "romaji": "Character Romaji",
                            "english": "Character English"
                        },
                        "type": "ANIME"
                    }
                },
                {
                    "relationType": "FAKERELATION",
                    "node": {
                        "id": 666,
                        "idMal": 666,
                        "title": {
                            "romaji": "Fake Romaji",
                            "english": "Fake English"
                        },
                        "type": "ANIME"
                    }
                },
                {
                    "relationType": "SEQUEL",
                    "node": {
                        "id": 185660,
                        "idMal": 60543,
                        "title": {
                            "romaji": "Sequel Romaji",
                            "english": "Sequel English"
                        },
                        "type": "ANIME"
                    }
                }
            ],
            []
        )

        expected = (
            [
                (
                    "Adaptation",
                    SearchResult(
                        id=132029,
                        id_mal=135496,
                        title_en="Adaptation English",
                        title_ro="Adaptation Romaji",
                        media_type="MANGA"
                    )
                ),
                (
                    "Sequel",
                    SearchResult(
                        id=185660,
                        id_mal=60543,
                        title_en="Sequel English",
                        title_ro="Sequel Romaji",
                        media_type="ANIME"
                    )
                ),
                (
                    "Character",
                    SearchResult(
                        id=185586,
                        id_mal=60461,
                        title_en="Character English",
                        title_ro="Character Romaji",
                        media_type="ANIME"
                    )
                ),
                (
                    "Fakerelation",
                    SearchResult(
                        id=666,
                        id_mal=666,
                        title_en="Fake English",
                        title_ro="Fake Romaji",
                        media_type="ANIME"
                    )
                )
            ],
            []
        )

        for i, elem in enumerate(data):
            with self.subTest(i=i):
                # Act
                res = await self.bot._parse_relations(elem)

                # Assert
                self.assertIsInstance(res, list)
                self.assertEqual(res, expected[i])

    async def test_parse_description(self):
        # Arrange
        data = [
            (
                {
                    "description": (
                        "Desctiption!<br><br>\n(Source: Crunchyroll) "
                        "<br><br>\n\nNotes: <br>\n- Some notes"
                    )
                },
                "Desctiption!<br><br>\n(Source: Crunchyroll) <br><br>\n\n"
            ),
            (
                {
                    "description": (
                        "Desctiption!<br><br>\n(Source: Crunchyroll) "
                        "<br><br>\n\nNote: <br>\n- A note"
                    )
                },
                "Desctiption!<br><br>\n(Source: Crunchyroll) <br><br>\n\n"
            ),
            (
                {
                    "description": None
                },
                ""
            )
        ]

        # Act
        for elem in data:
            with self.subTest():

                res = await self.bot._parse_description(elem[0])

                # Assert
                self.assertEqual(res, elem[1])

    async def test_parse_votes(self):
        # Arrange
        data = [
            (
                {
                    "stats": {
                        "scoreDistribution": None
                    }
                },
                0
            ),
            (
                {
                    "stats": {
                        "scoreDistribution": [
                            {
                                "amount": 9
                            },
                            {
                                "amount": 2
                            },
                            {
                                "amount": 2
                            },
                            {
                                "amount": 9
                            },
                            {
                                "amount": 27
                            },
                            {
                                "amount": 41
                            },
                            {
                                "amount": 186
                            },
                            {
                                "amount": 385
                            },
                            {
                                "amount": 408
                            },
                            {
                                "amount": 224
                            }
                        ]
                    }
                },
                1293
            ),
        ]

        # Act
        for elem in data:
            with self.subTest():

                res = await self.bot._parse_votes(elem[0])

                # Assert
                self.assertEqual(res, elem[1])

    async def test_parse_date(self):
        # Arrange
        data = [
            (
                {
                    "startDate": {
                        "day": 4,
                        "month": 10,
                        "year": 2024
                    }
                },
                "4 Oct 2024"
            ),
            (
                {
                    "endDate": {
                        "day": 20,
                        "month": 12,
                        "year": 2024
                    }
                },
                "20 Dec 2024"
            ),
            (
                {
                    "startDate": {
                        "day": None,
                        "month": 10,
                        "year": 2024
                    }
                },
                "Oct 2024"
            ),
            (
                {
                    "startDate": {
                        "day": None,
                        "month": None,
                        "year": 2024
                    }
                },
                "2024"
            ),
            (
                {
                    "startDate": {
                        "day": None,
                        "month": None,
                        "year": None
                    }
                },
                ""
            )
        ]

        # Act
        for elem in data:
            with self.subTest():

                res = await self.bot._parse_date(elem[0], list(elem[0].keys())[0])

                # Assert
                self.assertEqual(res, elem[1])

    async def test_parse_next_airing_episode(self):
        # Arrange
        data = [
            (
                {
                    "nextAiringEpisode": {
                        "airingAt": 1768143600,
                        "episode": 2
                    }
                },
                "Sunday, 11 Jan 2026, 16:00"
            ),
            (
                {
                    "nextAiringEpisode": {
                        "airingAt": None,
                        "episode": 2
                    }
                },
                None
            ),
            (
                {
                    "nextAiringEpisode": None,
                },
                None
            )
        ]

        # Act
        for elem in data:
            with self.subTest():

                res = await self.bot._parse_next_airing_episode(elem[0])

                # Assert
                self.assertEqual(res, elem[1])

    async def test_parse_studios(self):
        # Arrange
        data = [
            (
                {
                    "studios": {
                        "edges": [
                            {
                                "isMain": True,
                                "node": {
                                    "id": 6145,
                                    "name": "Science SARU"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 143,
                                    "name": "Mainichi Broadcasting System"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 6145,
                                    "name": "Science SARU"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 6570,
                                    "name": "Shueisha"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 53,
                                    "name": "Dentsu"
                                }
                            }
                        ]
                    },
                },
                ({('Science SARU', 6145)}, 4)
            ),
            (
                {
                    "studios": {
                        "edges": [
                            {
                                "isMain": True,
                                "node": {
                                    "id": 6145,
                                    "name": "Science SARU"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 143,
                                    "name": "Mainichi Broadcasting System"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 6145,
                                    "name": "Science SARU"
                                }
                            },
                            {
                                "isMain": True,
                                "node": {
                                    "id": 6570,
                                    "name": "Shueisha"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 53,
                                    "name": "Dentsu"
                                }
                            }
                        ]
                    },
                },
                ({('Science SARU', 6145), ('Shueisha', 6570)}, 3)
            ),
            (
                {
                    "studios": {
                        "edges": [
                            {
                                "isMain": False,
                                "node": {
                                    "id": 6145,
                                    "name": "Science SARU"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 143,
                                    "name": "Mainichi Broadcasting System"
                                }
                            },
                            {
                                "isMain": False,
                                "node": {
                                    "id": 62,
                                    "name": "Shogakukan-Shueisha Productions"
                                }
                            }
                        ]
                    },
                },
                ({('Science SARU', 6145)}, 2)
            ),
            (
                {
                    "studios": {
                        "edges": []
                    },
                },
                (set(), 0)
            )
        ]

        # Act
        for elem in data:
            with self.subTest():

                res = await self.bot._parse_studios(elem[0])

                # Assert
                self.assertEqual(res, elem[1])

    async def test_prepare_message_should_return_TextMessageEventContent(self):
        # Arrange
        animanga_data = AniMangaData(
            id=0,
            id_mal=0,
            title_ro="",
            title_en="",
            title_ja="",
            type="ANIME",
            image="",
            start_date="",
            end_date="",
            description="",
            average_score=0,
            mean_score=0,
            votes=0,
            favorites=0,
            nsfw=False,
            format="",
            status="",
            genres=[],
            tags=[],
            episodes=0,
            season="",
            season_year=0,
            next_episode_num=0,
            next_episode_date="",
            duration=0,
            relations=[],
            studios=set(),
            studio_number=0,
            links=[],
            volumes=0,
            chapters=0,
            trailer=()
        )
        search_results = []

        # Act
        result = await self.bot._prepare_message(animanga_data, search_results)

        # Assert
        self.assertIsInstance(result, TextMessageEventContent)

    async def test_get_max_value_when_incorrect_key_then_log_error_and_return_default(self):
        # Arrange
        config = ({"test": "bad_value"}, 5)
        self.bot.config = config[0]

        # Act
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            result = self.bot._get_max_value("test", 5)

            # Assert
            self.assertEqual(
                ["ERROR:testlogger:Incorrect 'test' config value. Setting default value of 5."],
                logger.output
            )
            self.assertEqual(result, config[1])

    async def test_get_matrix_image_url_when_request_is_successful_then_return_url(self):
        # Arrange
        data = b'image_data'
        self.bot.http.get = AsyncMock(
            return_value=await self.create_resp(200, resp_bytes=data, content_type="image/png")
        )
        self.bot.client.upload_media = AsyncMock(
            return_value="mxc://thumbnail.example.com/image.png"
        )

        # Act
        response = await self.bot.get_matrix_image_url("https://example.com/image.png")

        # Assert
        self.assertEqual(response, "mxc://thumbnail.example.com/image.png")

    async def test_get_matrix_image_url_when_aiohttp_ClientError_then_return_empty_string(self):
        # Arrange
        self.bot.http.get = AsyncMock(side_effect=aiohttp.ClientError)

        # Act
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            response = await self.bot.get_matrix_image_url("https://example.com/image.png")

            # Assert
            self.assertEqual(
                ['ERROR:testlogger:Downloading image - connection failed: '],
                logger.output
            )
            self.assertEqual(response, "")

    async def test_get_matrix_image_url_when_error_then_return_empty_string(self):
        # Arrange
        data = b'image_data'
        self.bot.http.get = AsyncMock(
            return_value=await self.create_resp(200, resp_bytes=data, content_type="image/png")
        )
        errors = (
            (ClientError, "Downloading image - connection failed: "),
            (ValueError, "Uploading image to Matrix server: "),
            (MatrixResponseError("test"), "Uploading image to Matrix server: test"))
        for error, log_message in errors:
            with self.subTest(error=error, log_message=log_message):
                self.bot.client.upload_media = AsyncMock(side_effect=error)

                # Act
                with self.assertLogs(self.bot.log, level='ERROR') as logger:
                    result = await self.bot.get_matrix_image_url("https://example.com/image.png")

                    # Assert
                    self.assertEqual([f"ERROR:testlogger:{log_message}"], logger.output)
                    self.assertEqual(result, "")

    async def test_get_link(self):
        # Arrange
        data = (
            (
                "<a href=\"https://html.example.com\">Example</a>",
                "https://html.example.com",
                "Example",
                True
            ),
            (
                "[Example](https://md.example.com)",
                "https://md.example.com",
                "Example",
                False
            )
        )

        for elem in data:
            with self.subTest():
                # Act
                res = await self.bot._get_link(elem[1], elem[2], elem[3])

            # Assert
            self.assertEqual(res, elem[0])

    async def test_get_titles(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                123,
                321,
                "English",
                "Romaji",
                "MANGA",
                True,
                (
                    '<h3><a href="https://anilist.co/manga/123">English</a> '
                    '<sup>(<a href="https://myanimelist.net/manga/321">MAL</a>)</sup> 🔞</h3>'
                ),
                True
            ),
            (
                123,
                0,
                "",
                "Romaji",
                "",
                False,
                '<h3><a href="https://anilist.co/anime/123">Romaji</a></h3>',
                True
            ),
            (
                123,
                321,
                "English",
                "Romaji",
                "MANGA",
                True,
                (
                    '> ### [English](https://anilist.co/manga/123) '
                    '([MAL](https://myanimelist.net/manga/321)) 🔞  \n>  \n'
                ),
                False
            ),
            (
                123,
                0,
                "",
                "Romaji",
                "",
                False,
                '> ### [Romaji](https://anilist.co/anime/123)  \n>  \n',
                False
            )
        )
        for elem in input_data:
            data.id = elem[0]
            data.id_mal = elem[1]
            data.title_en = elem[2]
            data.title_ro = elem[3]
            data.type = elem[4]
            data.nsfw = elem[5]
            result = elem[6]
            with self.subTest():
                # Act
                res = await self.bot._get_titles(data, elem[7])

                # Assert
                self.assertEqual(res, result)

    async def test_get_score(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                84,
                85,
                2137,
                69,
                (
                    '<blockquote><b>Score:</b> ⭐ 8.4/10 | 👤 2137 votes'
                    ' | ❤️ 69 favorites</blockquote>'
                ),
                True
            ),
            (
                None,
                85,
                None,
                None,
                '<blockquote><b>Score:</b> ⭐ 8.5/10</blockquote>',
                True
            ),
            (
                None,
                85,
                None,
                69,
                '<blockquote><b>Score:</b> ⭐ 8.5/10 | ❤️ 69 favorites</blockquote>',
                True
            ),
            (
                None,
                None,
                10,
                5,
                '',
                True
            ),
            (
                84,
                85,
                2137,
                69,
                '> > **Score**: ⭐ 8.4/10 | 👤 2137 votes | ❤️ 69 favorites  \n>  \n',
                False
            ),
        )
        for elem in input_data:
            data.average_score = elem[0]
            data.mean_score = elem[1]
            data.votes = elem[2]
            data.favorites = elem[3]
            result = elem[4]
            with self.subTest():
                # Act
                res = await self.bot._get_score(data, elem[5])

                # Assert
                self.assertEqual(res, result)

    async def test_get_description(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                "description<br><br>test",
                "<p>description<br>test</p>",
                True
            ),
            (
                None,
                (
                    ''
                ),
                True
            ),
            (
                "description<br><br>\r\ntest",
                "> description  \n> test  \n>  \n",
                False
            ),
        )
        for elem in input_data:
            data.description = elem[0]
            result = elem[1]
            with self.subTest():
                # Act
                res = await self.bot._get_description(data, elem[2])

                # Assert
                self.assertEqual(res, result)

    async def test_get_image(self):
        # Arrange
        input_data = (
            (
                "https://example.com",
                "Example alt",
                (5, 10),
                '<img src="https://example.com" alt="Example alt" width="5" height="10" />',
                True
            ),
            (
                "https://example.com",
                "Example alt",
                (0, 5),
                '<img src="https://example.com" alt="Example alt" height="5" />',
                True
            ),
            (
                "https://example.com",
                "Example alt",
                (5, 0),
                '<img src="https://example.com" alt="Example alt" width="5" />',
                True
            ),
            (
                "https://example.com",
                "Example alt",
                (0, 0),
                '<img src="https://example.com" alt="Example alt" />',
                True
            ),
            (
                "https://example.com",
                "Example alt",
                (5, 10),
                '![Example alt](https://example.com)',
                False
            ),
        )
        for elem in input_data:
            result = elem[3]
            with self.subTest():
                # Act
                res = await self.bot._get_image(elem[0], elem[1], elem[2], elem[4])

                # Assert
                self.assertEqual(res, result)

    async def test_get_main_table(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                "https://example.com",
                "Romaji",
                "English",
                "column",
                (
                    '<div><table><tr><td>column</td><td>'
                    '<img src="https://example.com" alt="Poster for English" height="230" />'
                    '</td></tr></table></div>'
                )
            ),
            (
                None,
                "Romaji",
                None,
                "column",
                "<table><tr><td>column</td></tr></table>"
            ),
            (
                "https://example.com",
                "Romaji",
                None,
                "column",
                (
                    '<div><table><tr><td>column</td><td>'
                    '<img src="https://example.com" alt="Poster for Romaji" height="230" />'
                    '</td></tr></table></div>'
                )
            ),
        )
        for elem in input_data:
            data.image = elem[0]
            data.title_ro = elem[1]
            data.title_en = elem[2]
            col = elem[3]
            result = elem[4]
            with self.subTest():
                # Act
                res = await self.bot._get_main_table(data, col)

                # Assert
                self.assertEqual(res, result)

    async def test_get_other_titles(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                "English",
                "Romaji",
                "Japanese",
                "<blockquote><b>Other titles:</b> Romaji, Japanese</blockquote>",
                True
            ),
            (
                None,
                "Romaji",
                "Japanese",
                "<blockquote><b>Other titles:</b> Japanese</blockquote>",
                True
            ),
            (
                None,
                "Romaji",
                None,
                "",
                True
            ),
            (
                "English",
                "Romaji",
                "Japanese",
                "> > **Other titles:** Romaji, Japanese  \n>  \n",
                False
            ),
        )
        for elem in input_data:
            data.title_en = elem[0]
            data.title_ro = elem[1]
            data.title_ja = elem[2]
            result = elem[3]
            with self.subTest():
                # Act
                res = await self.bot._get_other_titles(data, elem[4])

                # Assert
                self.assertEqual(res, result)

    async def test_get_format(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                "TV",
                12,
                24,
                0,
                0,
                "<blockquote><b>Format:</b> TV | 12 episodes (24 min per episode)</blockquote>",
                True
            ),
            (
                "Movie",
                1,
                118,
                0,
                0,
                "> > **Format**: Movie | 1 episode (1 h 58 min)  \n>  \n",
                False
            ),
            (
                "",
                12,
                24,
                0,
                0,
                "",
                True
            ),
            (
                "TV",
                0,
                24,
                0,
                0,
                "<blockquote><b>Format:</b> TV</blockquote>",
                True
            ),
            (
                "TV",
                12,
                0,
                0,
                0,
                "<blockquote><b>Format:</b> TV | 12 episodes</blockquote>",
                True
            ),
            (
                "TV",
                0,
                0,
                0,
                0,
                "<blockquote><b>Format:</b> TV</blockquote>",
                True
            ),
            (
                "Manga",
                0,
                0,
                4,
                50,
                "<blockquote><b>Format:</b> Manga | 4 volumes | 50 chapters</blockquote>",
                True
            ),
            (
                "Manga",
                0,
                0,
                0,
                50,
                "<blockquote><b>Format:</b> Manga | 50 chapters</blockquote>",
                True
            ),
            (
                "Manga",
                0,
                0,
                4,
                0,
                "<blockquote><b>Format:</b> Manga | 4 volumes</blockquote>",
                True
            )
        )
        for elem in input_data:
            data.format = elem[0]
            data.episodes = elem[1]
            data.duration = elem[2]
            data.volumes = elem[3]
            data.chapters = elem[4]
            result = elem[5]
            with self.subTest():
                # Act
                res = await self.bot._get_format(data, elem[6])

                # Assert
                self.assertEqual(res, result)

    async def test_get_status_next_episode(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                5,
                "Sunday, 11 Jan 2026, 16:00",
                "Releasing",
                (
                    "<blockquote><b>Status:</b> Releasing | "
                    "Episode 5 on Sunday, 11 Jan 2026, 16:00</blockquote>"
                ),
                True
            ),
            (
                5,
                "Sunday, 11 Jan 2026, 16:00",
                "Releasing",
                "> > **Status:** Releasing | Episode 5 on Sunday, 11 Jan 2026, 16:00  \n>  \n",
                False
            ),
            (
                0,
                "",
                "Finished",
                "<blockquote><b>Status:</b> Finished</blockquote>",
                True
            ),
            (
                5,
                "",
                "Finished",
                "<blockquote><b>Status:</b> Finished</blockquote>",
                True
            ),
            (
                0,
                "Sunday, 11 Jan 2026, 16:00",
                "Finished",
                "<blockquote><b>Status:</b> Finished</blockquote>",
                True
            ),
            (
                5,
                "Sunday, 11 Jan 2026, 16:00",
                "",
                "",
                False
            ),
        )
        for elem in input_data:
            data.next_episode_num = elem[0]
            data.next_episode_date = elem[1]
            data.status = elem[2]
            result = elem[3]
            with self.subTest():
                # Act
                res = await self.bot._get_status_next_episode(data, elem[4])

                # Assert
                self.assertEqual(res, result)

    async def test_get_dates_season(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                "29 Sep 2023",
                "22 Mar 2024",
                "TV Series",
                "Fall",
                2023,
                "<blockquote><b>Released:</b> 29 Sep 2023 to 22 Mar 2024 | Fall 2023</blockquote>",
                True
            ),
            (
                "",
                "22 Mar 2024",
                "TV Series",
                "Fall",
                2023,
                "<blockquote><b>Released:</b> Fall 2023</blockquote>",
                True
            ),
            (
                "29 Sep 2023",
                "29 Sep 2023",
                "TV Series",
                "Fall",
                2023,
                "<blockquote><b>Released:</b> 29 Sep 2023 | Fall 2023</blockquote>",
                True
            ),
            (
                "29 Sep 2023",
                "",
                "Movie",
                "Fall",
                2023,
                "<blockquote><b>Released:</b> 29 Sep 2023 | Fall 2023</blockquote>",
                True
            ),
            (
                "29 Sep 2023",
                "22 Mar 2024",
                "TV Series",
                "",
                2023,
                "<blockquote><b>Released:</b> 29 Sep 2023 to 22 Mar 2024</blockquote>",
                True
            ),
            (
                "29 Sep 2023",
                "22 Mar 2024",
                "TV Series",
                "Fall",
                0,
                "<blockquote><b>Released:</b> 29 Sep 2023 to 22 Mar 2024</blockquote>",
                True
            ),
            (
                "29 Sep 2023",
                "22 Mar 2024",
                "TV Series",
                "Fall",
                2023,
                "> > **Released:** 29 Sep 2023 to 22 Mar 2024 | Fall 2023  \n>  \n",
                False
            ),
            (
                "29 Sep 2023",
                "",
                "TV Series",
                "Fall",
                2023,
                "<blockquote><b>Released:</b> 29 Sep 2023 to ? | Fall 2023</blockquote>",
                True
            )
        )
        for elem in input_data:
            data.start_date = elem[0]
            data.end_date = elem[1]
            data.format = elem[2]
            data.season = elem[3]
            data.season_year = elem[4]
            result = elem[5]
            with self.subTest():
                # Act
                res = await self.bot._get_dates_season(data, elem[6])

                # Assert
                self.assertEqual(res, result)


if __name__ == '__main__':
    unittest.main()
