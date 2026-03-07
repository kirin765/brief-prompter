from dataclasses import dataclass


@dataclass
class CaptionService:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.client = None
        if settings.openai_api_key:
            from openai import AsyncOpenAI

            self.client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

    async def generate_caption(self, brief: str, transformed_prompt: str) -> str:
        fallback = self._short_fallback(brief)
        if self.settings.dry_run:
            return fallback
        if not self.client:
            return fallback
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Generate a short TikTok caption in {self.settings.caption_language}. "
                            "Keep it concise and engaging. Optional hashtags are fine."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Brief:\n{brief}\n\nPrompt:\n{transformed_prompt}",
                    },
                ],
                max_tokens=120,
                temperature=0.6,
            )
            content = response.choices[0].message.content.strip() if response.choices else fallback
            if not content:
                return fallback
            return self._shorten(content)
        except Exception:
            return fallback

    def _short_fallback(self, brief: str) -> str:
        words = brief.replace("\n", " ").split()
        caption = " ".join(words[:20]).strip()
        return self._shorten(caption)

    def _shorten(self, text: str) -> str:
        if len(text) <= self.settings.caption_length_limit:
            return text
        return text[: self.settings.caption_length_limit - 3].rstrip() + "..."
