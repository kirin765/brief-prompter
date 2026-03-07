from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import Settings, schedule_expression
from ..utils.logging import get_logger


class PipelineScheduler:
    def __init__(self, pipeline, settings: Settings) -> None:
        self.pipeline = pipeline
        self.settings = settings
        self.logger = get_logger(__name__)
        self._scheduler = AsyncIOScheduler(timezone=settings.app_timezone)

    def start(self) -> None:
        trigger = CronTrigger(
            hour=schedule_expression(self.settings),
            minute=0,
            timezone=self.settings.app_timezone,
        )
        self._scheduler.add_job(
            self._run_pipeline,
            trigger=trigger,
            id="brief_pipeline",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
            replace_existing=True,
        )
        self._scheduler.start()

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def _run_pipeline(self) -> None:
        if self._scheduler is None:
            return
        try:
            await self.pipeline.run_once()
        except Exception as exc:
            self.logger.error("Scheduled run failed", extra={"event": "scheduled_run_failed", "error": str(exc)})
