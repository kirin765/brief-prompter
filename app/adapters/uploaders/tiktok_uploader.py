from pathlib import Path

import httpx

from ..uploaders.base import UploadResult, SocialUploader


class TikTokUploader:
    def __init__(self, settings) -> None:
        self.settings = settings

    async def upload(self, video_path: str, caption: str) -> UploadResult:
        if not Path(video_path).exists():
            return UploadResult(
                upload_status="failed",
                success=False,
                error_message=f"Video path not found: {video_path}",
            )

        if self.settings.dry_run or not self.settings.tiktok_access_token:
            return UploadResult(
                upload_status="skipped_dry_run",
                success=True,
                post_id=None,
            )

        headers = {
            "Authorization": f"Bearer {self.settings.tiktok_access_token.get_secret_value()}",
        }
        timeout = httpx.Timeout(self.settings.http_timeout_sec)
        upload_url = f"{self.settings.tiktok_api_base.rstrip('/')}{self.settings.tiktok_upload_endpoint}"
        publish_url = f"{self.settings.tiktok_api_base.rstrip('/')}{self.settings.tiktok_publish_endpoint}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            with open(video_path, "rb") as fp:
                files = {"video": fp}
                response = await client.post(upload_url, files=files, headers=headers, data={"caption": caption})
                response.raise_for_status()
                uploaded = response.json()

            if not uploaded.get("success") and response.status_code >= 300:
                return UploadResult(
                    upload_status="failed",
                    success=False,
                    error_message=uploaded.get("message", "TikTok upload response indicates failure"),
                )

            media_id = uploaded.get("media_id") or uploaded.get("video_id") or uploaded.get("upload_id")
            if not media_id:
                return UploadResult(
                    upload_status="failed",
                    success=False,
                    error_message="TikTok upload returned no media id",
                )

            publish_payload = {
                "media_id": media_id,
                "caption": caption,
                "privacy_level": "PUBLIC",
            }
            publish_resp = await client.post(publish_url, headers=headers, json=publish_payload)
            publish_resp.raise_for_status()
            published = publish_resp.json()

            if not published.get("success") and publish_resp.status_code >= 300:
                return UploadResult(
                    upload_status="failed",
                    success=False,
                    error_message=published.get("message", "TikTok publish response indicates failure"),
                )

            post_id = published.get("post_id") or published.get("aweme_id")
            post_url = published.get("post_url")

            return UploadResult(
                upload_status="uploaded",
                success=True,
                post_id=post_id,
                post_url=post_url,
            )
