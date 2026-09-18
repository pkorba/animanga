import unittest

from mautrix.types import TextMessageEventContent
from animanga.resources.datastructures import AniMangaData, SearchResult
from .base_test import TestAniMangaBot

class TestAniMangaFormatters(TestAniMangaBot):
    async def test_prepare_message_should_return_TextMessageEventContent(self):
        # Arrange
        self.bot.fmt.config = {"use_mal_api": False}
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
            trailer=(),
            authors=[]
        )
        search_results = []

        # Act
        result = await self.bot.fmt.prepare_message(animanga_data, search_results)

        # Assert
        self.assertIsInstance(result, TextMessageEventContent)

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
                res = await self.bot.fmt._get_link(elem[1], elem[2], elem[3])

            # Assert
            self.assertEqual(res, elem[0])

    async def test_get_titles(self):
        # Arrange
        data = AniMangaData()
        self.bot.fmt.config = {"use_mal_api": False}
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
                res = await self.bot.fmt._get_titles(data, elem[7])

                # Assert
                self.assertEqual(res, result)

    async def test_get_score(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                840,
                850,
                2137,
                69,
                (
                    '<blockquote><b>Score:</b> ⭐ 8.4/10 | 👤 2 137 votes'
                    ' | ❤️ 69 favorites</blockquote>'
                ),
                True
            ),
            (
                0,
                850,
                None,
                None,
                '<blockquote><b>Score:</b> ⭐ 8.5/10</blockquote>',
                True
            ),
            (
                0,
                850,
                0,
                69,
                '<blockquote><b>Score:</b> ⭐ 8.5/10 | ❤️ 69 favorites</blockquote>',
                True
            ),
            (
                0,
                0,
                10,
                5,
                '',
                True
            ),
            (
                840,
                850,
                2137,
                69,
                '> > **Score**: ⭐ 8.4/10 | 👤 2 137 votes | ❤️ 69 favorites  \n>  \n',
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
                res = await self.bot.fmt._get_score(data, elem[5])

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
                res = await self.bot.fmt._get_description(data, elem[2])

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
                res = await self.bot.fmt._get_image(elem[0], elem[1], elem[2], elem[4])

                # Assert
                self.assertEqual(res, result)

    async def test_get_poster(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                "https://example.com",
                "Romaji",
                "English",
                (
                    '<img src="https://example.com" alt="Poster for English" '
                    'width="230" height="325" />'
                ),
                True
            ),
            (
                "https://example.com",
                "Romaji",
                "English",
                (
                    '![Poster for English](https://example.com)  \n>  \n'
                ),
                False
            ),
            (
                None,
                "Romaji",
                None,
                "",
                True
            ),
            (
                "https://example.com",
                "Romaji",
                None,
                (
                    '<img src="https://example.com" alt="Poster for Romaji" '
                    'width="230" height="325" />'
                ),
                True
            ),
            (
                "https://example.com",
                "Romaji",
                None,
                (
                    '![Poster for Romaji](https://example.com)  \n>  \n'
                ),
                False
            ),
        )
        for elem in input_data:
            data.image = elem[0]
            data.title_ro = elem[1]
            data.title_en = elem[2]
            result = elem[3]
            is_html = elem[4]
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_poster(data, is_html)

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
                res = await self.bot.fmt._get_other_titles(data, elem[4])

                # Assert
                self.assertEqual(res, result)

    async def test_get_format(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                "TV",
                12,
                "24 min",
                0,
                0,
                "<blockquote><b>Format:</b> TV | 12 episodes (24 min per episode)</blockquote>",
                True
            ),
            (
                "Movie",
                1,
                "1 h 58 min",
                0,
                0,
                "> > **Format**: Movie | 1 episode (1 h 58 min)  \n>  \n",
                False
            ),
            (
                "",
                12,
                "24 min",
                0,
                0,
                "",
                True
            ),
            (
                "TV",
                0,
                "24 min",
                0,
                0,
                "<blockquote><b>Format:</b> TV</blockquote>",
                True
            ),
            (
                "TV",
                12,
                "",
                0,
                0,
                "<blockquote><b>Format:</b> TV | 12 episodes</blockquote>",
                True
            ),
            (
                "TV",
                0,
                "",
                0,
                0,
                "<blockquote><b>Format:</b> TV</blockquote>",
                True
            ),
            (
                "Manga",
                0,
                "",
                4,
                50,
                "<blockquote><b>Format:</b> Manga | 4 volumes | 50 chapters</blockquote>",
                True
            ),
            (
                "Manga",
                0,
                "",
                0,
                50,
                "<blockquote><b>Format:</b> Manga | 50 chapters</blockquote>",
                True
            ),
            (
                "Manga",
                0,
                "",
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
                res = await self.bot.fmt._get_format(data, elem[6])

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
                res = await self.bot.fmt._get_status_next_episode(data, elem[4])

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
                res = await self.bot.fmt._get_dates_season(data, elem[6])

                # Assert
                self.assertEqual(res, result)

    async def test_get_studios(self):
        # Arrange
        data = AniMangaData()
        self.bot.fmt.config = {"use_mal_api": False}
        input_data = (
            (
                {("Studio Name", 123), ("Studio Name 1", 321)},
                5,
                [
                    '<blockquote><b>Studios:</b> '
                    '<a href="https://anilist.co/studio/321">Studio Name 1</a>, '
                    '<a href="https://anilist.co/studio/123">Studio Name</a> '
                    '+ 5 others</blockquote>',
                    '<blockquote><b>Studios:</b> '
                    '<a href="https://anilist.co/studio/123">Studio Name</a>, '
                    '<a href="https://anilist.co/studio/321">Studio Name 1</a> '
                    '+ 5 others</blockquote>',
                ],
                True
            ),
            (
                set(),
                0,
                [""],
                True
            ),
            (
                {("Studio Name", 123)},
                5,
                [
                    '> > **Studios:** [Studio Name](https://anilist.co/studio/123) '
                    '+ 5 others  \n>  \n'
                ],
                False
            ),
            (
                {("Studio Name", 123)},
                1,
                [
                    '<blockquote><b>Studios:</b> '
                    '<a href="https://anilist.co/studio/123">Studio Name</a> '
                    '+ 1 other</blockquote>'
                ],
                True
            ),
            (
                {("Studio Name", 123)},
                0,
                [
                    '<blockquote><b>Studios:</b> '
                    '<a href="https://anilist.co/studio/123">Studio Name</a>'
                    '</blockquote>'
                ],
                True
            ),
        )
        for elem in input_data:
            data.studios = elem[0]
            data.studio_number = elem[1]
            result = elem[2]
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_studios(data, elem[3])

                # Assert
                self.assertIn(res, result)

    async def test_get_links(self):
        # Arrange
        data = AniMangaData()
        input_data = (
            (
                [
                    ("Twitter", "https://twitter.example.com/anime_title"),
                    ("Official Site", "https://example.com/")
                ],
                ("youtube", "g59AsmwgRUY"),
                (
                    '<blockquote><b>External links:</b> '
                    '<a href="https://www.youtube.com/watch?v=g59AsmwgRUY">🎬 <b>TRAILER</b></a>, '
                    '<a href="https://twitter.example.com/anime_title">Twitter</a>, '
                    '<a href="https://example.com/">Official Site</a></blockquote>'
                ),
                True
            ),
            (
                [
                    ("Twitter", "https://twitter.example.com/anime_title"),
                    ("Official Site", "https://example.com/")
                ],
                ("notyoutube", "g59AsmwgRUY"),
                (
                    '<blockquote><b>External links:</b> '
                    '<a href="https://twitter.example.com/anime_title">Twitter</a>, '
                    '<a href="https://example.com/">Official Site</a></blockquote>'
                ),
                True
            ),
            (
                [
                    ("Twitter", "https://twitter.example.com/anime_title")
                ],
                ("youtube", ""),
                (
                    '<blockquote><b>External links:</b> '
                    '<a href="https://twitter.example.com/anime_title">Twitter</a></blockquote>'
                ),
                True
            ),
            (
                [],
                ("youtube", "g59AsmwgRUY"),
                (
                    '<blockquote><b>External links:</b> '
                    '<a href="https://www.youtube.com/watch?v=g59AsmwgRUY">🎬 <b>TRAILER</b></a>'
                    '</blockquote>'
                ),
                True
            ),
            (
                [
                    ("Twitter", "https://twitter.example.com/anime_title"),
                    ("Official Site", "https://example.com/")
                ],
                ("youtube", "g59AsmwgRUY"),
                (
                    '> > **External links:** '
                    '[🎬 **TRAILER**](https://www.youtube.com/watch?v=g59AsmwgRUY), '
                    '[Twitter](https://twitter.example.com/anime_title), '
                    '[Official Site](https://example.com/)  \n>  \n'
                ),
                False
            ),
        )
        for elem in input_data:
            data.links = elem[0]
            data.trailer = elem[1]
            result = elem[2]
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_links(data, elem[3])

                # Assert
                self.assertEqual(res, result)

    async def test_get_genres(self):
        # Arrange
        data = AniMangaData()
        self.bot.fmt.config = {"use_mal_api": False}
        input_data = (
            (
                [("Drama", 0), ("Slice of Life", 0)],
                "anime",
                (
                    '<blockquote><b>Genres:</b> '
                    '<a href="https://anilist.co/search/anime/Drama">Drama</a>, '
                    '<a href="https://anilist.co/search/anime/Slice%20of%20Life">Slice of Life</a>'
                    '</blockquote>'
                ),
                True
            ),
            (
                [("Drama", 0)],
                "manga",
                (
                    '<blockquote><b>Genres:</b> '
                    '<a href="https://anilist.co/search/manga/Drama">Drama</a>'
                    '</blockquote>'
                ),
                True
            ),
            (
                [],
                "manga",
                "",
                True
            ),
            (
                [("Drama", 0)],
                "",
                '> > **Genres:** [Drama](https://anilist.co/search/anime/Drama)  \n>  \n',
                False
            ),
        )
        for elem in input_data:
            data.genres = elem[0]
            data.type = elem[1]
            result = elem[2]
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_genres(data, elem[3])

                # Assert
                self.assertEqual(res, result)

    async def test_get_tags(self):
        # Arrange
        data = AniMangaData()
        self.bot.fmt.config = {"use_mal_api": False}
        input_data = (
            (
                [("Drama", 0), ("Slice of Life", 0)],
                "anime",
                (
                    '<blockquote><b>Tags:</b> '
                    '<a href="https://anilist.co/search/anime?genres=Drama">Drama</a>, '
                    '<a href="https://anilist.co/search/anime?genres=Slice%20of%20Life">'
                    'Slice of Life</a>'
                    '</blockquote>'
                ),
                True
            ),
            (
                [("Drama", 0)],
                "manga",
                (
                    '<blockquote><b>Tags:</b> '
                    '<a href="https://anilist.co/search/manga?genres=Drama">Drama</a>'
                    '</blockquote>'
                ),
                True
            ),
            (
                [],
                "manga",
                "",
                True
            ),
            (
                [("Drama", 0)],
                "",
                '> > **Tags:** [Drama](https://anilist.co/search/anime?genres=Drama)  \n>  \n',
                False
            ),
        )
        for elem in input_data:
            data.tags = elem[0]
            data.type = elem[1]
            result = elem[2]
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_tags(data, elem[3])

                # Assert
                self.assertEqual(res, result)

    async def test_get_related_entries(self):
        # Arrange
        data = AniMangaData()
        self.bot.fmt.config = {"use_mal_api": False}
        input_data = (
            (
                [
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
                            title_en='',
                            title_ro='Sequel Romaji',
                            media_type='ANIME')
                    ),
                    (
                        'Character',
                        SearchResult(
                            id=185586,
                            id_mal=0,
                            title_en='Character English',
                            title_ro='Character Romaji',
                            media_type='ANIME')
                    )
                ],
                '<b>Related entries:</b>'
                '<blockquote>[Adaptation]<br>'
                '1. <a href="https://anilist.co/manga/132029">Adaptation English</a> '
                '<sup>(<a href="https://myanimelist.net/manga/135496">MAL</a>)</sup>'
                '</blockquote>'
                '<blockquote>[Sequel]<br>'
                '2. <a href="https://anilist.co/anime/185660">Sequel Romaji</a> '
                '<sup>(<a href="https://myanimelist.net/anime/60543">MAL</a>)</sup>'
                '</blockquote>'
                '<blockquote>[Character]<br>'
                '3. <a href="https://anilist.co/anime/185586">Character English</a>'
                '</blockquote>',
                True
            ),
            (
                [
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
                            title_en='',
                            title_ro='Sequel Romaji',
                            media_type='ANIME')
                    ),
                    (
                        'Character',
                        SearchResult(
                            id=185586,
                            id_mal=0,
                            title_en='Character English',
                            title_ro='Character Romaji',
                            media_type='ANIME')
                    )
                ],
                '> **Related entries:**  \n>  \n'
                '> > 1. [Adaptation English](https://anilist.co/manga/132029) '
                '([MAL](https://myanimelist.net/manga/135496)) [Adaptation]  \n>  \n'
                '> > 2. [Sequel Romaji](https://anilist.co/anime/185660) '
                '([MAL](https://myanimelist.net/anime/60543)) [Sequel]  \n>  \n'
                '> > 3. [Character English](https://anilist.co/anime/185586) '
                '[Character]  \n>  \n',
                False
            ),
            (
                [],
                '',
                True
            ),
        )
        for elem in input_data:
            data.relations = elem[0]
            result = elem[1]
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_related_entries(data, elem[2])

                # Assert
                self.assertEqual(res, result)

    async def test_get_other_results(self):
        # Arrange
        data = AniMangaData()
        self.bot.fmt.config = {"use_mal_api": False}
        input_data = (
            (
                "anime",
                [
                    SearchResult(
                    id=132029,
                    id_mal=135496,
                    title_en='Adaptation English',
                    title_ro='Adaptation Romaji',
                    media_type='ANIME'
                    ),
                    SearchResult(
                        id=185660,
                        id_mal=60543,
                        title_en='',
                        title_ro='Sequel Romaji',
                        media_type='ANIME'
                    ),
                    SearchResult(
                        id=185586,
                        id_mal=0,
                        title_en='Character English',
                        title_ro='Character Romaji',
                        media_type='ANIME'
                    )
                ],
                '<b>Other results:</b>'
                '<blockquote>'
                '1. <a href="https://anilist.co/anime/185660">Sequel Romaji</a> '
                '<sup>(<a href="https://myanimelist.net/anime/60543">MAL</a>)</sup>'
                '</blockquote>'
                '<blockquote>'
                '2. <a href="https://anilist.co/anime/185586">Character English</a>'
                '</blockquote>',
                True
            ),
            (
                "manga",
                [
                    SearchResult(
                        id=132029,
                        id_mal=135496,
                        title_en='Adaptation English',
                        title_ro='Adaptation Romaji',
                        media_type='MANGA'
                    ),
                    SearchResult(
                        id=185660,
                        id_mal=60543,
                        title_en='',
                        title_ro='Sequel Romaji',
                        media_type='MANGA'
                    ),
                    SearchResult(
                        id=185586,
                        id_mal=0,
                        title_en='Character English',
                        title_ro='Character Romaji',
                        media_type='MANGA'
                    )
                ],
                '> **Other results:**  \n>  \n'
                '> > 1. [Sequel Romaji](https://anilist.co/manga/185660) '
                '([MAL](https://myanimelist.net/manga/60543))  \n>  \n'
                '> > 2. [Character English](https://anilist.co/manga/185586)  \n>  \n',
                False
            ),
            (
                "anime",
                [
                    SearchResult(
                        id=132029,
                        id_mal=135496,
                        title_en='Adaptation English',
                        title_ro='Adaptation Romaji',
                        media_type='ANIME'
                    )
                ],
                '',
                True
            ),
            (
                "",
                [],
                '',
                True
            ),
        )
        for elem in input_data:
            data.type = elem[0]
            other = elem[1]
            result = elem[2]
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_other_results(data, other, elem[3])

                # Assert
                self.assertEqual(res, result)

    async def test_get_links_section(self):
        # Arrange
        input_data = (
            (
                "col1",
                "col2",
                "<div>col1</div>"
                "<div>col2</div>"
            ),
            (
                "",
                "col2",
                "<div>col2</div>"
            ),
            (
                "col1",
                "",
                "<div>col1</div>"
            ),
            (
                "",
                "",
                ""
            )
        )
        for elem in input_data:
            col1 = elem[0]
            col2 = elem[1]
            result = elem[2]
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_links_section(col1, col2)

                # Assert
                self.assertEqual(res, result)

    async def test_get_details(self):
        # Arrange
        data = (
            (
                "<details><summary><b>title </b></summary>content</details>",
                "title",
                "content"
            ),
            (
                "",
                "",
                "content"
            ),
            (
                "",
                "title",
                ""
            )
        )

        for elem in data:
            with self.subTest():
                # Act
                res = await self.bot.fmt._get_details(elem[1], elem[2])

            # Assert
            self.assertEqual(res, elem[0])

if __name__ == '__main__':
    unittest.main()
