from dataclasses import dataclass
from typing import Optional
from typing import Protocol


@dataclass
class UploadResult:
    upload_status: str
    success: bool
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None


class SocialUploader(Protocol):
    async def upload(self, video_path: str, caption: str) -> UploadResult:
        ...
