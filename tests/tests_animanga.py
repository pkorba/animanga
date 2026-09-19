import unittest
from unittest.mock import AsyncMock

import aiohttp
from aiohttp import ClientError

from mautrix.errors.base import MatrixResponseError

from .base_test import TestAniMangaBot


class TestAniMangaBase(TestAniMangaBot):
    async def test_get_other_media_ids_when_other_results_then_return_media_ids(self):
        # Arrange
        test_vals = ((False, [130003, 101386, 165253]), (True, [47917, 37614, 55357]))
        body =  (
            "<blockquote><div><h3><a href=\"https://anilist.co/anime/102448\">Ouch, Chou Chou</a> "
            "<sup>(<a href=\"https://myanimelist.net/anime/34631\">MAL</a>)</sup></h3><blockquote>"
            "<b>Score:</b> ⭐ 4.3/10 | 👤 115 votes | ❤️ 2 favorites</blockquote></div><div><details>"
            "<summary><b>SYNOPSIS </b></summary><p>Old friends Cabbage and Pea reunite under "
            "awkward circumstances.</p></details></div><div><details><summary><b>POSTER </b>"
            "</summary><img src=\"mxc://e.com/lLlfzxXiFKLxJYjlvgXzENya\" alt=\"Poster for Ouch,"
            " Chou Chou\" width=\"230\" height=\"322\" /></details></div><div><details><summary>"
            "<b>DETAILS </b></summary><blockquote><b>Other titles:</b> Aitata Bocchi, あいたたぼっち"
            "</blockquote><blockquote><b>Format:</b> Special | 1 episode (11 min)</blockquote>"
            "<blockquote><b>Status:</b> Finished</blockquote><blockquote><b>Released:</b> 2016"
            "</blockquote><blockquote><b>External links:</b> "
            "<a href=\"https://vimeo.com/152551578\">Vimeo</a></blockquote><blockquote>"
            "<b>Genres:</b> <a href=\"https://anilist.co/search/anime/Drama\">Drama</a>"
            "</blockquote><blockquote><b>Tags:</b> "
            "<a href=\"https://anilist.co/search/anime?genres=Bullying\">Bullying</a></blockquote>"
            "</details></div><div><details><summary><b>LINKS </b></summary><div>"
            "<b>Other results:</b><blockquote>1. <a href=\"https://anilist.co/anime/130003\">"
            "BOCCHI THE ROCK!</a> <sup>(<a href=\"https://myanimelist.net/anime/47917\">MAL</a>)"
            "</sup></blockquote><blockquote>2. <a href=\"https://anilist.co/anime/101386\">"
            "Hitoribocchi no Marumaruseikatsu</a> <sup>"
            "(<a href=\"https://myanimelist.net/anime/37614\">MAL</a>)</sup></blockquote>"
            "<blockquote>3. <a href=\"https://anilist.co/anime/165253\">"
            "BOCCHI THE ROCK! Recap Part 1</a> <sup>"
            "(<a href=\"https://myanimelist.net/anime/55357\">MAL</a>)</sup></blockquote></div>"
            "</details></div><p><b><sub>Results from AniList</sub></b></p></blockquote>"
        )
        for use_mal_api, res in test_vals:
            with self.subTest(use_mal_api=use_mal_api, res=res):
                self.bot.config = {"use_mal_api": use_mal_api}

                # Act
                result = self.bot._get_other_media_ids(body)

                # Assert
                self.assertListEqual(result, res)

    async def test_get_other_media_ids_when_no_results_then_return_empty_list(self):
        # Arrange
        test_vals = (
            (False, "<b>Other results:</b></div>", []),
            (False, "", []),
            (True, "<b>Other results:</b></div>", []),
            (True, "", [])
        )

        for use_mal_api, body, res in test_vals:
            with self.subTest(use_mal_api=use_mal_api, res=res):
                self.bot.config = {"use_mal_api": use_mal_api}

                # Act
                result = self.bot._get_other_media_ids(body)

                # Assert
                self.assertListEqual(result, res)

    async def test_get_matrix_image_url_when_request_is_successful_then_return_url(self):
        # Arrange
        data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x05\x00\x00\x00\n\x08\x06'
            b'\x00\x00\x00|9\x940\x00\x00\x00\tpHYs\x00\x00\x0e\xc4\x00\x00\x0e\xc4\x01'
            b'\x95+\x0e\x1b\x00\x00\x00\x15IDAT\x08\x99c\xfc\xff\xff\xff\x7f\x064\xc0'
            b'\x84.0\x94\x04\x01C\xf5\x04\x10\xadS\xf5\xda\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        self.bot.http.get = AsyncMock(
            return_value=await self.create_resp(200, resp_bytes=data, content_type="image/png")
        )
        self.bot.client.upload_media = AsyncMock(
            return_value="mxc://thumbnail.example.com/image.png"
        )

        # Act
        response = await self.bot._get_matrix_image_url("https://example.com/image.png")

        # Assert
        self.assertEqual(response, "mxc://thumbnail.example.com/image.png")

    async def test_get_matrix_image_url_when_aiohttp_ClientError_then_return_empty_string(self):
        # Arrange
        self.bot.http.get = AsyncMock(side_effect=aiohttp.ClientError)

        # Act
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            response = await self.bot._get_matrix_image_url("https://example.com/image.png")

            # Assert
            self.assertListEqual(
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
                    result = await self.bot._get_matrix_image_url("https://example.com/image.png")

                    # Assert
                    self.assertListEqual([f"ERROR:testlogger:{log_message}"], logger.output)
                    self.assertEqual(result, "")

    async def test_get_image_dimensions_when_correct_data_then_return_dimensions(self):
        # Arrange
        # white 5x10 png rectangle
        image = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x05\x00\x00\x00\n\x08\x06'
            b'\x00\x00\x00|9\x940\x00\x00\x00\tpHYs\x00\x00\x0e\xc4\x00\x00\x0e\xc4\x01'
            b'\x95+\x0e\x1b\x00\x00\x00\x15IDAT\x08\x99c\xfc\xff\xff\xff\x7f\x064\xc0'
            b'\x84.0\x94\x04\x01C\xf5\x04\x10\xadS\xf5\xda\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # Act
        width, height = self.bot._get_image_dimensions(image)

        # Assert
        self.assertEqual(width, 5)
        self.assertEqual(height, 10)

    async def test_get_image_dimensions_when_error_then_return_default_values(self):
        # Arrange
        image = "string"
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            # Act
            width, height = self.bot._get_image_dimensions(image)

            # Assert
            self.assertEqual(width, 230)
            self.assertEqual(height, 325)
            self.assertListEqual(
                [
                    "ERROR:testlogger:Error reading image dimensions: "
                    "a bytes-like object is required, not 'str'"
                ],
                logger.output
            )

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
                self.bot.pr.config = config_dict

                # Act
                result = self.bot.pr.get_max_value("test", 5)

                # Assert
                self.assertEqual(result, expected_result)

    async def test_get_max_value_when_incorrect_key_then_log_error_and_return_default(self):
        # Arrange
        config = ({"test": "bad_value"}, 5)
        self.bot.pr.config = config[0]

        # Act
        with self.assertLogs(self.bot.log, level='ERROR') as logger:
            result = self.bot.pr.get_max_value("test", 5)

            # Assert
            self.assertListEqual(
                ["ERROR:testlogger:Incorrect 'test' config value. Setting default value of 5."],
                logger.output
            )
            self.assertEqual(result, config[1])

if __name__ == '__main__':
    unittest.main()
