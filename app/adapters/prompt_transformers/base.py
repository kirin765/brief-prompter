from typing import Protocol


class PromptTransformer(Protocol):
    async def transform(self, brief: str) -> str:
        ...
