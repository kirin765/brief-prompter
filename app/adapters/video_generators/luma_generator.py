import asyncio
import time
from pathlib import Path
from typing import Optional

import httpx

from ..video_generators.base import VideoGenerationResult, VideoGenerator
from ...utils.retry import retry_async
from ...utils.files import ensure_directory, write_placeholder_video


class LumaGenerator:
    def __init__(self, settings) -> None:
        self.settings = settings

    async def generate(self, prompt: str, metadata: Optional[dict] = None) -> VideoGenerationResult:
        job_id = (metadata or {}).get("job_id", "pipeline")
        if self.settings.dry_run or not self.settings.luma_api_key:
            output_path = f"data/output/{job_id}.mp4"
            ensure_directory(output_path)
            write_placeholder_video(output_path)
            return VideoGenerationResult(
                generation_id=f"dryrun-{job_id}",
                status="completed",
                asset_url=None,
                local_video_path=output_path,
                status_history=[{"status": "completed", "source": "dry_run"}],
            )

        headers = {
            "Authorization": f"Bearer {self.settings.luma_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(self.settings.http_timeout_sec)

        payload = {
            "prompt": prompt,
            "model": self.settings.luma_model,
            "aspect_ratio": "9:16",
            "metadata": (metadata or {}),
        }

        async def start_generation() -> dict:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(self.settings.luma_generation_endpoint, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        started = await retry_async(
            start_generation,
            retries=self.settings.max_retries,
            initial_delay=self.settings.retry_initial_delay,
            max_delay=self.settings.retry_max_delay,
        )
        generation_id = str(started.get("id") or started.get("generation_id"))
        if not generation_id:
            raise RuntimeError("Luma API response missing generation id")

        status_history: list[dict] = []
        deadline = time.monotonic() + self.settings.luma_timeout_sec

        while time.monotonic() < deadline:
            async def check_status() -> dict:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(
                        self.settings.luma_status_endpoint.format(generation_id=generation_id),
                        headers=headers,
                    )
                    response.raise_for_status()
                    return response.json()

            result = await retry_async(
                check_status,
                retries=max(0, self.settings.max_retries - 1),
                initial_delay=self.settings.retry_initial_delay,
                max_delay=self.settings.retry_max_delay,
            )
            status = str(result.get("status", result.get("state", "unknown"))).lower()
            status_history.append({"status": status, "details": result})

            if status in {"succeeded", "completed", "ready", "finished"}:
                asset_url = (
                    result.get("video_url")
                    or result.get("output_url")
                    or (result.get("assets") or {}).get("video")
                )
                if not asset_url:
                    raise RuntimeError("Luma generation completed but no output URL returned")
                output_path = f"data/output/{job_id}.mp4"
                await self._download(asset_url, output_path)
                return VideoGenerationResult(
                    generation_id=generation_id,
                    status=status,
                    asset_url=asset_url,
                    local_video_path=output_path,
                    status_history=status_history,
                )

            if status in {"failed", "error", "canceled", "cancelled", "expired"}:
                raise RuntimeError(f"Luma generation failed with status: {status}")

            await asyncio.sleep(self.settings.luma_poll_interval_sec)

        raise TimeoutError("Luma generation timed out")

    async def _download(self, url: str, output_path: str) -> None:
        timeout = httpx.Timeout(self.settings.http_timeout_sec)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.content
            ensure_directory(output_path)
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
