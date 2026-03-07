from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..db.models import JobStatus


class JobOut(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    raw_brief_snapshot: str | None = None
    transformed_prompt: str | None = None
    luma_generation_id: str | None = None
    luma_status: str | None = None
    luma_asset_url: str | None = None
    local_video_path: str | None = None
    tiktok_caption: str | None = None
    tiktok_upload_status: str | None = None
    tiktok_post_id: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class JobList(BaseModel):
    jobs: list[JobOut]


class BriefRefreshResponse(BaseModel):
    brief: str


class RunOnceResponse(BaseModel):
    job_id: str
    status: JobStatus


class RetryResponse(BaseModel):
    job_id: str
    status: JobStatus


class ErrorResponse(BaseModel):
    detail: str


class StatusMessage(BaseModel):
    status: str
    details: dict[str, Any] = Field(default_factory=dict)
