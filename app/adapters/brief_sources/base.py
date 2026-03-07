from typing import Protocol


class BriefSource(Protocol):
    async def fetch_latest(self) -> str:
        ...
