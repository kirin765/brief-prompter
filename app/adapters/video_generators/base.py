from dataclasses import dataclass
from typing import Protocol, Optional


@dataclass
class VideoGenerationResult:
    generation_id: str
    status: str
    asset_url: Optional[str]
    local_video_path: Optional[str] = None
    status_history: Optional[list[dict]] = None


class VideoGenerator(Protocol):
    async def generate(self, prompt: str, metadata: Optional[dict] = None) -> VideoGenerationResult:
        ...
