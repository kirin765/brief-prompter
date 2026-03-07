from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    BRIEF_FETCHED = "brief_fetched"
    PROMPT_GENERATED = "prompt_generated"
    VIDEO_GENERATING = "video_generating"
    VIDEO_READY = "video_ready"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    job_type: Mapped[str] = mapped_column(String, default="scheduled")
    status: Mapped[str] = mapped_column(String, default=JobStatus.QUEUED)

    raw_brief_snapshot: Mapped[str | None] = mapped_column(Text)
    transformed_prompt: Mapped[str | None] = mapped_column(Text)

    luma_generation_id: Mapped[str | None] = mapped_column(String)
    luma_status: Mapped[str | None] = mapped_column(String)
    luma_asset_url: Mapped[str | None] = mapped_column(String)
    luma_status_history: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)

    local_video_path: Mapped[str | None] = mapped_column(String)

    tiktok_caption: Mapped[str | None] = mapped_column(Text)
    tiktok_upload_status: Mapped[str | None] = mapped_column(String)
    tiktok_post_id: Mapped[str | None] = mapped_column(String)

    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
