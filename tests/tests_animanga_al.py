import unittest
from unittest.mock import AsyncMock

from aiohttp import ClientError

from animanga.resources.datastructures import AniMangaData, SearchResult
from .base_test import TestAniMangaBot

class TestAniMangaAl(TestAniMangaBot):
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
        results = await self.bot.pr.al_parse_results(data)

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
            results = await self.bot.pr.al_parse_results(data)

            # Assert
            self.assertEqual(
                ["ERROR:testlogger:Error parsing results: Error message; Error message 2"],
                logger.output
            )
            self.assertEqual(results, [])

    async def test_al_parse_main_result_when_correct_anime_data_return_AniMangaData(self):
        # Arrange
        self.bot.pr.config = {}
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
        result = await self.bot.pr.al_parse_main_result(data)

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
            "Desctiption!<br><br>\n(Source: Crunchyroll) <br><br>"
        )
        self.assertEqual(result.average_score, 840)
        self.assertEqual(result.mean_score, 850)
        self.assertEqual(result.votes, 113412)
        self.assertEqual(result.favorites, 15063)
        self.assertEqual(result.nsfw, True)
        self.assertEqual(result.format, "TV Show")
        self.assertEqual(result.status, "Finished")
        self.assertEqual(
            result.genres,
            [
                ("Action", 0),
                ("Comedy", 0),
                ("Drama", 0),
                ("Romance", 0),
                ("Sci-Fi", 0),
                 ("Supernatural", 0)
             ]
        )
        self.assertEqual(result.tags, [("Urban Fantasy", 0), ("Youkai", 0), ("Ghost", 0)])
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
        self.assertEqual(result.duration, "24 min")
        self.assertEqual(result.studios, {("Studio 1", 6145), ("Studio 4", 53)})
        self.assertEqual(result.studio_number, 3)
        self.assertEqual(result.trailer, ('youtube', 'qwertyuiopa'))
        self.assertEqual(result.volumes, 0)
        self.assertEqual(result.chapters, 0)

    async def test_al_parse_main_result_when_no_anime_data_return_empty_AniMangaData(self):
        # Arrange
        self.bot.pr.config = {}
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
                    "externalLinks": [],
                    "staff": {
                        "edges": []
                    }
                }
            }
        }

        # Act
        result = await self.bot.pr.al_parse_main_result(data)

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
        self.assertEqual(result.average_score, 0)
        self.assertEqual(result.mean_score, 0)
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
        self.assertEqual(result.next_episode_num, 0)
        self.assertEqual(result.next_episode_date, "")
        self.assertEqual(result.duration, "")
        self.assertEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ())
        self.assertEqual(result.volumes, 0)
        self.assertEqual(result.chapters, 0)
        self.assertEqual(result.authors, [])

    async def test_al_parse_main_result_when_correct_manga_data_return_AniMangaData(self):
        # Arrange
        self.bot.pr.config = {}
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
                    ],
                    "staff": {
                        "edges": [
                            {
                                "role": "Story & Art",
                                "node": {
                                    "id": 119917,
                                    "name": {
                                        "full": "Tatsuki Fujimoto"
                                    }
                                }
                            },
                            {
                                "role": "Assistant",
                                "node": {
                                    "id": 153964,
                                    "name": {
                                        "full": "Tokushige  Kawakatsu"
                                    }
                                }
                            },
                        ]
                    }
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
        result = await self.bot.pr.al_parse_main_result(data)

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
            "Desctiption!<br><br>\n(Source: VIZ Media) <br><br>"
        )
        self.assertEqual(result.average_score, 840)
        self.assertEqual(result.mean_score, 850)
        self.assertEqual(result.votes, 113412)
        self.assertEqual(result.favorites, 15063)
        self.assertEqual(result.nsfw, True)
        self.assertEqual(result.format, "Manga")
        self.assertEqual(result.status, "Finished")
        self.assertEqual(
            result.genres,
            [
                ("Action", 0),
                ("Comedy", 0),
                ("Drama", 0),
                ("Romance", 0),
                ("Sci-Fi", 0),
                ("Supernatural", 0)
            ]
        )
        self.assertEqual(result.tags, [("Urban Fantasy", 0), ("Youkai", 0), ("Ghost", 0)])
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
        self.assertEqual(result.duration, "")
        self.assertEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ())
        self.assertEqual(result.volumes, 5)
        self.assertEqual(result.chapters, 100)
        self.assertEqual(result.authors, [("Tatsuki Fujimoto", "Story & Art", 119917)])

    async def test_al_parse_main_result_when_no_manga_data_return_empty_AniMangaData(self):
        # Arrange
        self.bot.pr.config = {}
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
                    "externalLinks": [],
                    "staff": {
                        "edges": []
                    }
                }
            }
        }

        # Act
        result = await self.bot.pr.al_parse_main_result(data)

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
        self.assertEqual(result.average_score, 0)
        self.assertEqual(result.mean_score, 0)
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
        self.assertEqual(result.duration, "")
        self.assertEqual(result.studios, set())
        self.assertEqual(result.studio_number, 0)
        self.assertEqual(result.trailer, ())
        self.assertEqual(result.volumes, None)
        self.assertEqual(result.chapters, None)
        self.assertEqual(result.authors, [])

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
            results = await self.bot.pr.al_parse_main_result(data)

            # Assert
            self.assertEqual(
                ["ERROR:testlogger:Error parsing results: Error message; Error message 2"],
                logger.output
            )
            self.assertEqual(results, None)


if __name__ == '__main__':
    unittest.main()
