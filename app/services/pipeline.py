from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

import asyncio

from ..config import Settings
from ..db.models import Job, JobStatus
from ..db.session import session_scope
from ..adapters.brief_sources.base import BriefSource
from ..adapters.prompt_transformers.base import PromptTransformer
from ..adapters.video_generators.base import VideoGenerator
from ..adapters.uploaders.base import SocialUploader, UploadResult


class PipelineService:
    def __init__(
        self,
        settings: Settings,
        brief_source: BriefSource,
        prompt_transformer: PromptTransformer,
        video_generator: VideoGenerator,
        uploader: SocialUploader,
        caption_service,
        session_factory=session_scope,
    ) -> None:
        self.settings = settings
        self.brief_source = brief_source
        self.prompt_transformer = prompt_transformer
        self.video_generator = video_generator
        self.uploader = uploader
        self.caption_service = caption_service
        self.session_factory = session_factory
        self._run_lock = asyncio.Lock()

    async def run_once(self, *, dry_run: Optional[bool] = None) -> Job:
        async with self._run_lock:
            return await self._run_job(dry_run=dry_run)

    async def retry_job(self, job_id: str) -> Job:
        async with self._run_lock:
            return await self._run_job(job_id=job_id)

    async def refresh_brief_only(self) -> str:
        return await self.brief_source.fetch_latest()

    def list_jobs(self, *, limit: int = 100) -> list[Job]:
        with self.session_scope() as db:
            rows = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
            return rows

    def get_job(self, job_id: str) -> Optional[Job]:
        with self.session_scope() as db:
            return db.query(Job).filter(Job.job_id == job_id).first()

    @contextmanager
    def session_scope(self):
        with self.session_factory(self.settings.database_url) as session:
            yield session

    async def _run_job(self, job_id: Optional[str] = None, dry_run: Optional[bool] = None) -> Job:
        selected_dry_run = bool(self.settings.dry_run if dry_run is None else dry_run)
        now = datetime.now(timezone.utc)
        previous_dry_run = self.settings.dry_run
        self.settings.dry_run = selected_dry_run
        job = None
        db_session = None
        try:
            with self.session_scope() as db:
                db_session = db
                if job_id:
                    job = db.query(Job).filter(Job.job_id == job_id).first()
                    if job is None:
                        raise ValueError(f"Job not found: {job_id}")
                    if job.status != JobStatus.FAILED:
                        raise ValueError("Only failed jobs can be retried")
                    job.status = JobStatus.QUEUED
                    job.retry_count = (job.retry_count or 0) + 1
                    job.error_message = None
                else:
                    job = Job(
                        job_type="scheduled" if not selected_dry_run else "manual_dryrun",
                        status=JobStatus.QUEUED,
                        retry_count=0,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(job)
                db.commit()
                db.refresh(job)

                job.started_at = None
                job.completed_at = None
                job.raw_brief_snapshot = None
                job.transformed_prompt = None
                job.luma_generation_id = None
                job.luma_status = None
                job.luma_asset_url = None
                job.luma_status_history = None
                job.local_video_path = None
                job.tiktok_caption = None
                job.tiktok_upload_status = None
                job.tiktok_post_id = None
                db.commit()

                self._set_status(job, JobStatus.RUNNING, db)

                raw_brief = await self.brief_source.fetch_latest()
                job.raw_brief_snapshot = raw_brief
                self._set_status(job, JobStatus.BRIEF_FETCHED, db)

                transformed = await self.prompt_transformer.transform(raw_brief)
                job.transformed_prompt = transformed
                self._set_status(job, JobStatus.PROMPT_GENERATED, db)

                self._set_status(job, JobStatus.VIDEO_GENERATING, db)
                generation = await self.video_generator.generate(
                    transformed,
                    metadata={"job_id": job.job_id},
                )
                job.luma_generation_id = generation.generation_id
                job.luma_status = generation.status
                job.luma_status_history = generation.status_history
                job.luma_asset_url = generation.asset_url
                job.local_video_path = generation.local_video_path
                self._set_status(job, JobStatus.VIDEO_READY, db)

                job.tiktok_caption = await self.caption_service.generate_caption(raw_brief, transformed)
                self._set_status(job, JobStatus.UPLOADING, db)
                upload_result: UploadResult = await self.uploader.upload(
                    video_path=job.local_video_path,
                    caption=job.tiktok_caption,
                )

                job.tiktok_upload_status = upload_result.upload_status
                job.tiktok_post_id = upload_result.post_id

                if upload_result.success:
                    self._set_status(job, JobStatus.UPLOADED, db)
                else:
                    raise RuntimeError(upload_result.error_message or "Upload failed")

                db.commit()
                return job
        except Exception as exc:
            if db_session is not None and job is not None:
                self._fail_job(job, str(exc), db_session)
            raise
        finally:
            self.settings.dry_run = previous_dry_run

    def _set_status(self, job: Job, status: JobStatus, db) -> None:
        now = datetime.now(timezone.utc)
        job.status = status
        job.updated_at = now
        if status == JobStatus.RUNNING:
            job.started_at = now
        if status in {JobStatus.UPLOADED, JobStatus.FAILED}:
            job.completed_at = now
        db.commit()

    def _fail_job(self, job: Job, message: str, db) -> None:
        job.status = JobStatus.FAILED
        job.error_message = message
        job.updated_at = datetime.now(timezone.utc)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()



def build_pipeline(settings: Settings):
    from ..adapters.brief_sources.local_file import LocalFileBriefSource
    from ..adapters.prompt_transformers.openai_transformer import OpenAIPromptTransformer
    from ..adapters.video_generators.luma_generator import LumaGenerator
    from ..adapters.uploaders.tiktok_uploader import TikTokUploader
    from .caption_service import CaptionService
    from ..db.session import session_scope as default_session_scope

    brief_source = LocalFileBriefSource(settings.brief_file_path)
    prompt_transformer = OpenAIPromptTransformer(settings)
    video_generator = LumaGenerator(settings)
    uploader = TikTokUploader(settings)
    caption_service = CaptionService(settings)
    return PipelineService(
        settings=settings,
        brief_source=brief_source,
        prompt_transformer=prompt_transformer,
        video_generator=video_generator,
        uploader=uploader,
        caption_service=caption_service,
        session_factory=default_session_scope,
    )
