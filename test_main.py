import json
import unittest
from io import BytesIO
from unittest.mock import Mock, patch

from fastapi import UploadFile
from starlette.requests import Request

from main import index, video_to_gif


class VideoToGifAppTests(unittest.IsolatedAsyncioTestCase):
    def test_index_renders_upload_interface(self):
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [],
            }
        )

        response = index(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Chuyển đổi sang GIF", response.body.decode("utf-8"))
        self.assertIn('id="upload-form"', response.body.decode("utf-8"))
        self.assertIn('id="gif-link"', response.body.decode("utf-8"))
        self.assertIn('id="download-link"', response.body.decode("utf-8"))

    async def test_video_to_gif_rejects_non_mp4_upload(self):
        upload = UploadFile(filename="sample.txt", file=BytesIO(b"not-mp4"))

        response = await video_to_gif(upload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.body),
            {
                "status": "error",
                "message": "Chỉ hỗ trợ file .mp4",
            },
        )

    @patch("main.subprocess.run")
    async def test_video_to_gif_returns_public_gif_url_without_duration_limit(
        self,
        mock_run,
    ):
        mock_run.return_value = Mock(returncode=0)
        upload = UploadFile(filename="sample.mp4", file=BytesIO(b"fake-mp4"))

        response = await video_to_gif(upload)

        self.assertEqual(
            response,
            {
                "status": "success",
                "gif_url": response["gif_url"],
            },
        )
        self.assertTrue(response["gif_url"].startswith("/outputs/"))
        self.assertTrue(response["gif_url"].endswith(".gif"))

        command = mock_run.call_args.args[0]
        self.assertNotIn("-t", command)
        self.assertIn(
            "fps=8,scale=480:320:force_original_aspect_ratio=increase,crop=480:320",
            command,
        )


if __name__ == "__main__":
    unittest.main()
