from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field

from ..db.models import JobStatus


class JobOut(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    raw_brief_snapshot: Optional[str] = None
    transformed_prompt: Optional[str] = None
    luma_generation_id: Optional[str] = None
    luma_status: Optional[str] = None
    luma_asset_url: Optional[str] = None
    local_video_path: Optional[str] = None
    tiktok_caption: Optional[str] = None
    tiktok_upload_status: Optional[str] = None
    tiktok_post_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

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
