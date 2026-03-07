import asyncio
import re

from ..prompt_transformers.base import PromptTransformer


class OpenAIPromptTransformer:
    """Convert raw creative brief into concise Luma-ready prompt."""

    def __init__(self, settings) -> None:
        self.settings = settings
        self.client = None
        if settings.openai_api_key:
            from openai import AsyncOpenAI

            self.client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

    def _sanitize_brief(self, brief: str) -> str:
        text = brief
        text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)
        banned_lines = [
            r"^\s*\[.*?\]\s*\n?",
            r"(?im)^\s*(shot|컷|scene|씬|scene by scene).*\n?",
            r"(?im)^.*(cta|call to action|구독|좋아요|공유|팔로우|댓글|링크).*\n?",
            r"(?im)^.*(hashtag|#\S+).*$",
            r"(?im)^.*(subtitle|자막|caption).*\n?",
            r"(?im)^.*(sound cue|bgm|background music|오디오|음향).*\n?",
            r"(?im)^.*(instagram|youtube|tiktok|platform|platform metadata|vertical|9:16|landscape|landscape mode).*$",
        ]
        for pattern in banned_lines:
            text = re.sub(pattern, " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    async def transform(self, brief: str) -> str:
        cleaned = self._sanitize_brief(brief)
        if not self.client:
            return self._shorten(cleaned)

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a prompt engineer for Luma Dream Machine. "
                                "Input is a marketing brief; output only a short vertical short-form video prompt. "
                                "Keep visible scene content, subject, action, environment, style. "
                                "Do not include timestamps, shot-by-shot cues, CTA, hashtags, subtitles, platform metadata, or sound instructions."
                            ),
                        },
                        {"role": "user", "content": cleaned},
                    ],
                    temperature=0.2,
                ),
                timeout=20,
            )
            content = response.choices[0].message.content if response.choices else ""
            if not content:
                return self._shorten(cleaned)
            return self._shorten(content.strip())
        except Exception:
            return self._shorten(cleaned)

    def _shorten(self, text: str, max_len: int = 300) -> str:
        text = text.strip().replace("\n", " ")
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= max_len:
            return text
        return text[: max_len - 3].rstrip() + "..."
