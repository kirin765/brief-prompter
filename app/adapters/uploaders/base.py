from dataclasses import dataclass
from typing import Protocol


@dataclass
class UploadResult:
    upload_status: str
    success: bool
    post_id: str | None = None
    post_url: str | None = None
    error_message: str | None = None


class SocialUploader(Protocol):
    async def upload(self, video_path: str, caption: str) -> UploadResult:
        ...
