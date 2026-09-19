import unittest

from animanga.resources.datastructures import SearchResult
from .base_test import TestAniMangaBot


class TestAniMangaParsers(TestAniMangaBot):
    async def test_al_parse_duration(self):
        # Arrange
        config = (
            (0, ""),
            (59, "59 min"),
            (60, "1 h"),
            (61, "1 h 1 min"),
            (120, "2 h"),
            (150, "2 h 30 min"),
        )
        for minutes, expected_result in config:
            with self.subTest(minutes=minutes, expected_result=expected_result):
                # Act
                result = await self.bot.pr._al_parse_duration(minutes)

                # Assert
                self.assertEqual(result, expected_result)

    async def test_mal_parse_duration(self):
        # Arrange
        config = (
            ("", ""),
            ("Unknown", ""),
            ("59 min", "59 min"),
            ("59 min per ep", "59 min"),
            ("1 h", "1 h")
        )
        for minutes, expected_result in config:
            with self.subTest(minutes=minutes, expected_result=expected_result):
                # Act
                result = await self.bot.pr._mal_parse_duration(minutes)

                # Assert
                self.assertEqual(result, expected_result)

    async def test_al_parse_relations(self):
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
                res = await self.bot.pr._al_parse_relations(elem)

                # Assert
                self.assertIsInstance(res, list)
                self.assertEqual(res, expected[i])

    async def test_mal_parse_relations(self):
        # Arrange
        data = (
            [
                {
                    "relation": "Adaptation",
                    "entry":[
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
                    "entry":[
                        {
                            "mal_id": 23390,
                            "type": "manga",
                            "name": "Sequel Romaji",
                        }
                    ]
                },
                {
                    "relation": "Character",
                    "entry":[
                        {
                            "mal_id": 18397,
                            "type": "anime",
                            "name": "Character Romaji",
                        }
                    ]
                }
            ],
            []
        )

        expected = (
            [
                (
                    "Adaptation",
                    SearchResult(
                        id=19581,
                        id_mal=0,
                        title_en="",
                        title_ro="Adaptation Romaji 1",
                        media_type="ANIME"
                    )
                ),
                (
                    "Adaptation",
                    SearchResult(
                        id=35557,
                        id_mal=0,
                        title_en="",
                        title_ro="Adaptation Romaji 2",
                        media_type="ANIME"
                    )
                ),
                (
                    "Sequel",
                    SearchResult(
                        id=23390,
                        id_mal=0,
                        title_en="",
                        title_ro="Sequel Romaji",
                        media_type="MANGA"
                    )
                ),
                (
                    "Character",
                    SearchResult(
                        id=18397,
                        id_mal=0,
                        title_en="",
                        title_ro="Character Romaji",
                        media_type="ANIME"
                    )
                )
            ],
            []
        )

        for i, elem in enumerate(data):
            with self.subTest(i=i):
                # Act
                res = await self.bot.pr._mal_parse_relations(elem)

                # Assert
                self.assertIsInstance(res, list)
                self.assertListEqual(res, expected[i])

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
                "Desctiption!<br><br>\n(Source: Crunchyroll) <br><br>"
            ),
            (
                {
                    "description": (
                        "Desctiption!<br><br>\n(Source: Crunchyroll) "
                        "<br><br>\n\nNote: <br>\n- A note"
                    )
                },
                "Desctiption!<br><br>\n(Source: Crunchyroll) <br><br>"
            ),
            (
                {
                    "description": (
                        "Desctiption!<br><br>\n(Source: Crunchyroll) "
                        "<br><br>\n\n<i>Note: <br>\n- A note"
                    )
                },
                "Desctiption!<br><br>\n(Source: Crunchyroll) <br><br>\n\n"
            ),
            (
                {
                    "description": (
                        "Desctiption!<br><br>\n(Source: Crunchyroll) "
                        "<br><br><i> Note: <br>\n- A note"
                    )
                },
                "Desctiption!<br><br>\n(Source: Crunchyroll) <br><br>"
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

                res = await self.bot.pr._parse_description(elem[0])

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

                res = await self.bot.pr._parse_votes(elem[0])

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

                res = await self.bot.pr._parse_date(elem[0], list(elem[0].keys())[0])

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
                ""
            ),
            (
                {
                    "nextAiringEpisode": None,
                },
                ""
            )
        ]

        # Act
        for elem in data:
            with self.subTest():

                res = await self.bot.pr._parse_next_airing_episode(elem[0])

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

                res = await self.bot.pr._parse_studios(elem[0])

                # Assert
                self.assertEqual(res, elem[1])

    async def test_parse_authors(self):
        # Arrange
        data = (
            ([
                {
                    "role": "Story",
                    "node": {
                        "id": 119917,
                        "name": {
                            "full": "Tatsuki Fujimoto"
                        }
                    }
                },
                {
                    "role": "Art",
                    "node": {
                        "id": 153964,
                        "name": {
                            "full": "Tokushige  Kawakatsu"
                        }
                    }
                },
                {
                    "role": "Bottomless Pit Supervisor",
                    "node": {
                        "id": 2137,
                        "name": {
                            "full": "Hugh Mungus"
                        }
                    }
                }
            ], [
                ("Tatsuki Fujimoto", "Story", 119917),
                ("Tokushige  Kawakatsu", "Art", 153964)
            ]),
            ([], [])
        )

        # Act
        for elem in data:
            with self.subTest():
                res = await self.bot.pr._parse_authors(elem[0])

                # Assert
                self.assertListEqual(res, elem[1])

if __name__ == '__main__':
    unittest.main()
