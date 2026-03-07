from dataclasses import dataclass
from typing import Protocol


@dataclass
class VideoGenerationResult:
    generation_id: str
    status: str
    asset_url: str | None
    local_video_path: str | None = None
    status_history: list[dict] | None = None


class VideoGenerator(Protocol):
    async def generate(self, prompt: str, metadata: dict | None = None) -> VideoGenerationResult:
        ...
