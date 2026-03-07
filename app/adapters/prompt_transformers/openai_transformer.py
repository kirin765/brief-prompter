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

        system_prompt = (
            "You convert short-form creative briefs into concise prompts optimized for Luma Dream Machine video generation.\n\n"
            "Your task:\n"
            "- Read the user's creative brief.\n"
            "- Extract only what should be visually shown in the video.\n"
            "- Rewrite it as one clean Luma-ready prompt.\n\n"
            "Rules:\n"
            "- Remove timestamps.\n"
            "- Remove editing instructions such as rapid cuts, jump cuts, zoom cues, transitions, pacing notes, and sound cues.\n"
            "- Remove on-screen text, captions, hashtags, CTA language, platform strategy notes, and output formatting requests.\n"
            "- Keep only visible subject, action, environment, progression, and final reveal.\n"
            "- Keep the result grounded and specific.\n"
            "- Prefer 5 to 7 sentences.\n"
            "- Assume a vertical 9:16 short-form video.\n"
            "- End with a short style clause such as clean background, bright or cinematic lighting, realistic motion, fast-paced social media style.\n"
            "- Do not output bullet points.\n"
            "- Do not explain your choices.\n"
            "- Return only the final prompt text.\n"
        )
        user_prompt = (
            "Transform the following creative brief into a single Luma Dream Machine prompt.\n\n"
            f"Brief:\n{cleaned}"
        )

        try:
            payload = {
                "model": self.settings.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_output_tokens": 160,
            }
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**payload),
                timeout=20,
            )
            content = response.choices[0].message.content if response.choices else ""
            if not content:
                return self._shorten(cleaned)
            return self._shorten(content.strip())
        except TypeError:
            # Chat completion endpoint may reject max_output_tokens in some SDK versions.
            fallback_payload = {
                "model": self.settings.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 160,
            }
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**fallback_payload),
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
