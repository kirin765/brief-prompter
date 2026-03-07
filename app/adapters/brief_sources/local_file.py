import asyncio
from pathlib import Path

from .base import BriefSource


class LocalFileBriefSource:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    async def fetch_latest(self) -> str:
        return await asyncio.to_thread(self._read_file)

    def _read_file(self) -> str:
        path = Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"Brief file not found: {path}")
        data = path.read_text(encoding="utf-8").strip()
        if not data:
            raise ValueError("Brief file is empty")
        return data
