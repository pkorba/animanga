import unittest
from unittest.mock import AsyncMock

from aiohttp import ClientError

from animanga.resources.datastructures import AniMangaData, SearchResult
from .base_test import TestAniMangaBot


class TestAniMangaMal(TestAniMangaBot):
    async def test_mal_get_results_when_request_is_successful_then_return_json(self):
        # Arrange
        json_data = {"test": 1}
        self.bot.http.get = AsyncMock(return_value=await self.create_resp(200, json=json_data))

        # Act
        json_response = await self.bot._mal_get_results({"json": "test"}, "ANIME")

        # Assert
        self.assertDictEqual(json_response, json_data)

    async def test_mal_get_results_when__aiohttp_error_then_raise_exception(self):
        # Arrange
        self.bot.http.get = AsyncMock(side_effect=ClientError)

        # Assert
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            with self.assertRaisesRegex(ClientError, "Connection to Tenrai API failed."):
                # Act
                await self.bot._mal_get_results({"json": "test"}, "ANIME")
            self.assertListEqual(
                ['ERROR:testlogger:Connection to Tenrai API failed: '],
                logger.output
            )

    async def test_mal_get_main_result_when_request_is_successful_then_return_json(self):
        # Arrange
        json_data = {"test": 1}
        self.bot.http.get = AsyncMock(return_value=await self.create_resp(200, json=json_data))

        # Act
        json_response = await self.bot._mal_get_main_result(10, "ANIME")

        # Assert
        self.assertDictEqual(json_response, json_data)

    async def test_mal_get_main_result_when__aiohttp_error_then_raise_exception(self):
        # Arrange
        self.bot.http.get = AsyncMock(side_effect=ClientError)

        # Assert
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            with self.assertRaisesRegex(ClientError, "Connection to Tenrai API failed."):
                # Act
                await self.bot._mal_get_main_result(10, "ANIME")
            self.assertListEqual(
                ['ERROR:testlogger:Connection to Tenrai API failed: '],
                logger.output
            )

    async def test_mal_parse_results_when_correct_data_return_list_of_SearchResult(self):
        # Arrange
        data = {
            "data": [
                {
                    "mal_id": 16498,
                    "title": "Shingeki no Kyojin",
                    "title_english": "Attack on Titan",
                },
                {
                    "mal_id": 25777,
                    "title": "Shingeki no Kyojin Season 2",
                    "title_english": "Attack on Titan Season 2",
                },
                {
                    "mal_id": 35760,
                    "title": "Shingeki no Kyojin Season 3",
                    "title_english": "Attack on Titan Season 3",
                }
            ]
        }

        expected_results = [
            SearchResult(
                id=16498,
                id_mal=0,
                title_en="Attack on Titan",
                title_ro="Shingeki no Kyojin",
            ),
            SearchResult(
                id=25777,
                id_mal=0,
                title_en="Attack on Titan Season 2",
                title_ro="Shingeki no Kyojin Season 2",
            ),
            SearchResult(
                id=35760,
                id_mal=0,
                title_en="Attack on Titan Season 3",
                title_ro="Shingeki no Kyojin Season 3",
            )
        ]

        # Act
        results = await self.bot.pr.mal_parse_results(data)

        # Assert
        self.assertIsInstance(results[0], SearchResult)
        self.assertListEqual(results, expected_results)

    async def test_mal_parse_results_when_error_return_empty_list(self):
        # Arrange
        data = {
            "status": 400,
            "type": "BadRequestException",
            "message": "Bad request.",
            "error": "The request is malformed or not shaped like a supported Tenrai API request.",
            "path": "/v1/anime"
        }

        # Act
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            results = await self.bot.pr.mal_parse_results(data)

            # Assert
            self.assertListEqual(
                ["ERROR:testlogger:Error parsing results: Bad request."],
                logger.output
            )
            self.assertListEqual(results, [])

    async def test_mal_parse_main_result_when_correct_anime_data_return_AniMangaData(self):
        # Arrange
        self.bot.pr.config = {}
        data = {
            "data": {
                "mal_id": 16498,
                "url": "https://myanimelist.net/anime/16498/Romaji",
                "images": {
                    "webp": {
                        "image_url": "https://cdn.myanimelist.net/images/anime/10/47347.webp"
                    }
                },
                "trailer": {
                    "youtube_id": "qwertyuiopa"
                },
                "title": "Romaji",
                "title_english": "English",
                "title_japanese": "Native",
                "type": "TV",
                "episodes": 25,
                "status": "Finished Airing",
                "aired": {
                    "prop": {
                        "from": {
                            "day": 7,
                            "month": 4,
                            "year": 2013
                        },
                        "to": {
                            "day": 29,
                            "month": 9,
                            "year": 2013
                        }
                    },
                },
                "duration": "24 min per ep",
                "score": 8.58,
                "scored_by": 3110963,
                "favorites": 192225,
                "synopsis": "Description",
                "season": "spring",
                "year": 2013,
                "broadcast": {
                    "string": "Sundays at 01:58 (JST)"
                },
                "producers": [
                    {
                        "mal_id": 10,
                        "name": "Production I.G",
                    },
                    {
                        "mal_id": 53,
                        "name": "Dentsu",
                    }
                ],
                "licensors": [
                    {
                        "mal_id": 102,
                        "name": "Funimation",
                    }
                ],
                "studios": [
                    {
                        "mal_id": 2137,
                        "name": "Studio 1",
                    }
                ],
                "genres": [
                    {
                        "mal_id": 1,
                        "name": "Action",
                    },
                    {
                        "mal_id": 46,
                        "name": "Award Winning",
                    }
                ],
                "explicit_genres": [],
                "themes": [
                    {
                        "mal_id": 58,
                        "name": "Gore",
                    },
                    {
                        "mal_id": 38,
                        "name": "Military",
                    }
                ],
                "demographics": [
                    {
                        "mal_id": 27,
                        "name": "Shounen",
                    }
                ],
                "relations": [
                    {
                        "relation": "Adaptation",
                        "entry": [
                            {
                                "mal_id": 25777,
                                "type": "manga",
                                "name": "Adaptation Romaji",
                            }
                        ]
                    },
                    {
                        "relation": "Sequel",
                        "entry": [
                            {
                                "mal_id": 23390,
                                "type": "anime",
                                "name": "Sequel Romaji",
                            }
                        ]
                    },
                    {
                        "relation": "Character",
                        "entry": [
                            {
                                "mal_id": 18397,
                                "type": "anime",
                                "name": "Character Romaji",
                            }
                        ]
                    }
                ],
                "external": [
                    {
                        "name": "Twitter",
                        "url": "https://twitter.example.com/anime_title"
                    },
                    {
                        "name": "Official Site",
                        "url": "https://example.com/"
                    }
                ],
                "streaming": [
                    {
                        "name": "Crunchyroll",
                        "url": "http://www.crunchyroll.com/series-2137"
                    },
                    {
                        "name": "Netflix",
                        "url": "https://www.netflix.com/title/2137"
                    }
                ]
            }
        }
        relations = [
            (
                'Adaptation',
                SearchResult(
                    id=25777,
                    id_mal=0,
                    title_en='',
                    title_ro='Adaptation Romaji',
                    media_type='MANGA')
            ),
            (
                'Sequel',
                SearchResult(
                    id=23390,
                    id_mal=0,
                    title_en='',
                    title_ro='Sequel Romaji',
                    media_type='ANIME')
            ),
            (
                'Character',
                SearchResult(
                    id=18397,
                    id_mal=0,
                    title_en='',
                    title_ro='Character Romaji',
                    media_type='ANIME')
            )]

        # Act
        result = await self.bot.pr.mal_parse_main_result(data)

        # Assert
        self.assertIsInstance(result, AniMangaData)
        self.assertEqual(result.id, 16498)
        self.assertEqual(result.id_mal, 0)
        self.assertEqual(result.title_ro, "Romaji")
        self.assertEqual(result.title_en, "English")
        self.assertEqual(result.title_ja, "Native")
        self.assertEqual(result.type, "ANIME")
        self.assertEqual(
            result.image,
            "https://cdn.myanimelist.net/images/anime/10/47347.webp"
        )
        self.assertEqual(result.start_date, "7 Apr 2013")
        self.assertEqual(result.end_date, "29 Sep 2013")
        self.assertEqual(result.description, "Description")
        self.assertEqual(result.average_score, 858)
        self.assertEqual(result.mean_score, 858)
        self.assertEqual(result.votes, 3110963)
        self.assertEqual(result.favorites, 192225)
        self.assertEqual(result.nsfw, False)
        self.assertEqual(result.format, "TV")
        self.assertEqual(result.status, "Finished Airing")
        self.assertListEqual(result.genres, [("Action", 1),("Award Winning", 46)])
        self.assertListEqual(result.tags, [("Gore", 58), ("Military", 38), ("Shounen", 27)])
        self.assertListEqual(result.relations, relations)
        self.assertListEqual(
            result.links,
            [
                ("Twitter", "https://twitter.example.com/anime_title"),
                ("Official Site", "https://example.com/"),
                ("Crunchyroll", "http://www.crunchyroll.com/series-2137"),
                ("Netflix", "https://www.netflix.com/title/2137")
            ]
        )
        self.assertEqual(result.episodes, 25)
        self.assertEqual(result.season, "Spring")
        self.assertEqual(result.season_year, 2013)
        self.assertEqual(result.next_episode_num, 0)
        self.assertEqual(result.next_episode_date, "Sundays at 01:58 (JST)")
        self.assertEqual(result.duration, "24 min")
        self.assertSetEqual(result.studios, {("Studio 1", 2137)})
        self.assertEqual(result.studio_number, 3)
        self.assertEqual(result.trailer, ('youtube', 'qwertyuiopa'))
        self.assertEqual(result.volumes, 0)
        self.assertEqual(result.chapters, 0)
        self.assertListEqual(result.authors, [])

    async def test_mal_parse_main_result_when_no_anime_data_return_empty_AniMangaData(self):
        # Arrange
        self.bot.pr.config = {}
        data = {
            "data": {
                "mal_id": 171018,
                "url": "https://myanimelist.net/anime/171018/Romaji",
                "images": {
                    "webp": {
                        "image_url": None
                    }
                },
                "trailer": {
                    "youtube_id": None
                },
                "title": "Romaji",
                "title_english": None,
                "title_japanese": None,
                "type": None,
                "episodes": None,
                "status": None,
                "aired": {
                    "prop": {
                        "from": {
                            "day": None,
                            "month": None,
                            "year": None
                        },
                        "to": {
                            "day": None,
                            "month": None,
                            "year": None
                        }
                    },
                },
                "duration": "Unknown",
                "score": None,
                "scored_by": 0,
                "favorites": 0,
                "synopsis": None,
                "season": None,
                "year": None,
                "broadcast": {
                    "string": None
                },
                "producers": [],
                "licensors": [],
                "studios": [],
                "genres": [],
                "explicit_genres": [],
                "themes": [],
                "demographics": [],
                "relations": [],
                "external": [],
                "streaming": []
            }
        }

        # Act
        result = await self.bot.pr.mal_parse_main_result(data)

        # Assert
        self.assertIsInstance(result, AniMangaData)
        self.assertEqual(result.id, 171018)
        self.assertEqual(result.id_mal, 0)
        self.assertEqual(result.title_ro, "Romaji")
        self.assertEqual(result.title_en, None)
        self.assertEqual(result.title_ja, None)
        self.assertEqual(result.type, "ANIME")
        self.assertEqual(result.image, None)
        self.assertEqual(result.start_date, "")
        self.assertEqual(result.end_date, "")
        self.assertEqual(result.description, None)
        self.assertEqual(result.average_score, 0)
        self.assertEqual(result.mean_score, 0)
        self.assertEqual(result.votes, 0)
        self.assertEqual(result.favorites, 0)
        self.assertEqual(result.nsfw, False)
        self.assertEqual(result.format, None)
        self.assertEqual(result.status, None)
        self.assertListEqual(result.genres, [])
        self.assertListEqual(result.tags, [])
        self.assertListEqual(result.relations, [])
        self.assertListEqual(result.links, [])
        self.assertEqual(result.episodes, None)
        self.assertEqual(result.season, "")
        self.assertEqual(result.season_year, None)
        self.assertEqual(result.next_episode_num, 0)
        self.assertEqual(result.next_episode_date, None)
        self.assertEqual(result.duration, "")
        self.assertSetEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ("youtube", None))
        self.assertEqual(result.volumes, 0)
        self.assertEqual(result.chapters, 0)
        self.assertListEqual(result.authors, [])

    async def test_mal_parse_main_result_when_correct_manga_data_return_AniMangaData(self):
        # Arrange
        self.bot.pr.config = {}
        data = {
            "data": {
                "mal_id": 44489,
                "url": "https://myanimelist.net/manga/44489/Romaji",
                "images": {
                    "webp": {
                        "image_url": "https://cdn.myanimelist.net/images/manga/1/115443.webp"
                    }
                },
                "title": "Romaji",
                "title_english": "English",
                "title_japanese": "Native",
                "type": "Manga",
                "chapters": 108,
                "volumes": 13,
                "status": "Finished",
                "published": {
                    "prop": {
                        "from": {
                            "day": 25,
                            "month": 10,
                            "year": 2012
                        },
                        "to": {
                            "day": 25,
                            "month": 4,
                            "year": 2024
                        }
                    },
                },
                "score": 9,
                "scored_by": 61907,
                "favorites": 19842,
                "synopsis": "Description",
                "authors": [
                    {
                        "mal_id": 16515,
                        "name": "Ichikawa, Haruko",
                        "role": "Story & Art"
                    }
                ],
                "genres": [
                    {
                        "mal_id": 1,
                        "name": "Action",
                    },
                    {
                        "mal_id": 8,
                        "name": "Drama",
                    },
                    {
                        "mal_id": 10,
                        "name": "Fantasy",
                    }
                ],
                "explicit_genres": [],
                "themes": [
                    {
                        "mal_id": 51,
                        "name": "Anthropomorphic",
                    }
                ],
                "demographics": [
                    {
                        "mal_id": 41,
                        "name": "Seinen",
                    }
                ],
                "relations": [
                    {
                        "relation": "Adaptation",
                        "entry": [
                            {
                                "mal_id": 19581,
                                "type": "anime",
                                "name": "Adaptation Romaji 1",
                            },
                            {
                                "mal_id": 35557,
                                "type": "anime",
                                "name": "Adaptation Romaji 2",
                            }
                        ]
                    },
                    {
                        "relation": "Sequel",
                        "entry": [
                            {
                                "mal_id": 23390,
                                "type": "manga",
                                "name": "Sequel Romaji",
                            }
                        ]
                    },
                    {
                        "relation": "Character",
                        "entry": [
                            {
                                "mal_id": 18397,
                                "type": "anime",
                                "name": "Character Romaji",
                            }
                        ]
                    }
                ],
                "external": [
                    {
                        "name": "Twitter",
                        "url": "https://twitter.example.com/anime_title"
                    },
                    {
                        "name": "Official Site",
                        "url": "https://example.com/"
                    }
                ],
            }
        }
        relations = [
            (
                'Adaptation',
                SearchResult(
                    id=19581,
                    id_mal=0,
                    title_en='',
                    title_ro='Adaptation Romaji 1',
                    media_type='ANIME')
            ),
            (
                'Adaptation',
                SearchResult(
                    id=35557,
                    id_mal=0,
                    title_en='',
                    title_ro='Adaptation Romaji 2',
                    media_type='ANIME')
            ),
            (
                'Sequel',
                SearchResult(
                    id=23390,
                    id_mal=0,
                    title_en='',
                    title_ro='Sequel Romaji',
                    media_type='MANGA')
            ),
            (
                'Character',
                SearchResult(
                    id=18397,
                    id_mal=0,
                    title_en='',
                    title_ro='Character Romaji',
                    media_type='ANIME')
            )]

        # Act
        result = await self.bot.pr.mal_parse_main_result(data)

        # Assert
        self.assertIsInstance(result, AniMangaData)
        self.assertEqual(result.id, 44489)
        self.assertEqual(result.id_mal, 0)
        self.assertEqual(result.title_ro, "Romaji")
        self.assertEqual(result.title_en, "English")
        self.assertEqual(result.title_ja, "Native")
        self.assertEqual(result.type, "MANGA")
        self.assertEqual(
            result.image,
            "https://cdn.myanimelist.net/images/manga/1/115443.webp"
        )
        self.assertEqual(result.start_date, "25 Oct 2012")
        self.assertEqual(result.end_date, "25 Apr 2024")
        self.assertEqual(result.description, "Description")
        self.assertEqual(result.average_score, 900)
        self.assertEqual(result.mean_score, 900)
        self.assertEqual(result.votes, 61907)
        self.assertEqual(result.favorites, 19842)
        self.assertEqual(result.nsfw, False)
        self.assertEqual(result.format, "Manga")
        self.assertEqual(result.status, "Finished")
        self.assertListEqual(
            result.genres,
            [
                ("Action", 1),
                ("Drama", 8),
                ("Fantasy", 10)
            ]
        )
        self.assertListEqual(result.tags, [("Anthropomorphic", 51), ("Seinen", 41)])
        self.assertListEqual(result.relations, relations)
        self.assertListEqual(
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
        self.assertEqual(result.duration, "")
        self.assertSetEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ())
        self.assertEqual(result.volumes, 13)
        self.assertEqual(result.chapters, 108)
        self.assertListEqual(result.authors, [("Ichikawa, Haruko", "Story & Art", 16515)])

    async def test_mal_parse_main_result_when_no_manga_data_return_empty_AniMangaData(self):
        # Arrange
        self.bot.pr.config = {}
        data = {
            "data": {
                "mal_id": 44489,
                "url": "https://myanimelist.net/manga/44489/Romaji",
                "images": {
                    "webp": {
                        "image_url": None
                    }
                },
                "title": "Romaji",
                "title_english": None,
                "title_japanese": None,
                "type": None,
                "chapters": None,
                "volumes": None,
                "status": None,
                "published": {
                    "prop": {
                        "from": {
                            "day": None,
                            "month": None,
                            "year": None
                        },
                        "to": {
                            "day": None,
                            "month": None,
                            "year": None
                        }
                    },
                },
                "score": None,
                "scored_by": 0,
                "favorites": 0,
                "synopsis": None,
                "authors": [],
                "genres": [],
                "explicit_genres": [],
                "themes": [],
                "demographics": [],
                "relations": [],
                "external": []
            }
        }


        # Act
        result = await self.bot.pr.mal_parse_main_result(data)

        # Assert
        self.assertIsInstance(result, AniMangaData)
        self.assertEqual(result.id, 44489)
        self.assertEqual(result.id_mal, 0)
        self.assertEqual(result.title_ro, "Romaji")
        self.assertEqual(result.title_en, None)
        self.assertEqual(result.title_ja, None)
        self.assertEqual(result.type, "MANGA")
        self.assertEqual(result.image, None)
        self.assertEqual(result.start_date, "")
        self.assertEqual(result.end_date, "")
        self.assertEqual(result.description, None)
        self.assertEqual(result.average_score, 0)
        self.assertEqual(result.mean_score, 0)
        self.assertEqual(result.votes, 0)
        self.assertEqual(result.favorites, 0)
        self.assertEqual(result.nsfw, False)
        self.assertEqual(result.format, None)
        self.assertEqual(result.status, None)
        self.assertListEqual(result.genres, [])
        self.assertListEqual(result.tags, [])
        self.assertListEqual(result.relations, [])
        self.assertListEqual(result.links, [])
        self.assertEqual(result.episodes, 0)
        self.assertEqual(result.season, "")
        self.assertEqual(result.season_year, 0)
        self.assertEqual(result.next_episode_num, 0)
        self.assertEqual(result.next_episode_date, "")
        self.assertEqual(result.duration, "")
        self.assertSetEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ())
        self.assertEqual(result.volumes, None)
        self.assertEqual(result.chapters, None)
        self.assertListEqual(result.authors, [])

    async def test_mal_parse_main_result_when_error_return_None(self):
        # Arrange
        data = {
            "status": 403,
            "type": "ForbiddenException",
            "message": "Access temporarily blocked.",
            "error": "This IP is temporarily blocked due to abusive request patterns.",
            "path": "/v1/manga/1/full"
        }

        # Act
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            results = await self.bot.pr.mal_parse_main_result(data)

            # Assert
            self.assertListEqual(
                ["ERROR:testlogger:Error parsing results: Access temporarily blocked."],
                logger.output
            )
            self.assertEqual(results, None)

if __name__ == '__main__':
    unittest.main()
