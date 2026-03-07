from datetime import datetime
from typing import Optional
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

    raw_brief_snapshot: Mapped[Optional[str]] = mapped_column(Text)
    transformed_prompt: Mapped[Optional[str]] = mapped_column(Text)

    luma_generation_id: Mapped[Optional[str]] = mapped_column(String)
    luma_status: Mapped[Optional[str]] = mapped_column(String)
    luma_asset_url: Mapped[Optional[str]] = mapped_column(String)
    luma_status_history: Mapped[Optional[list[dict]]] = mapped_column(JSON, nullable=True)

    local_video_path: Mapped[Optional[str]] = mapped_column(String)

    tiktok_caption: Mapped[Optional[str]] = mapped_column(Text)
    tiktok_upload_status: Mapped[Optional[str]] = mapped_column(String)
    tiktok_post_id: Mapped[Optional[str]] = mapped_column(String)

    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
