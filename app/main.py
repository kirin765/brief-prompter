from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db.session import init_db
from .schemas.jobs import BriefRefreshResponse, JobList, JobOut, RunOnceResponse, RetryResponse
from .services.pipeline import build_pipeline, PipelineService
from .services.scheduler import PipelineScheduler
from .utils.logging import configure_logging


async def get_pipeline(request: Request) -> PipelineService:
    return request.app.state.pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db(settings.database_url)

    pipeline = build_pipeline(settings)
    scheduler = PipelineScheduler(pipeline, settings)
    app.state.pipeline = pipeline
    app.state.scheduler = scheduler

    if settings.enable_scheduler:
        scheduler.start()

    yield

    scheduler.stop()


app = FastAPI(
    title="brief-prompter",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs", response_model=JobList)
async def list_jobs(request: Request, limit: int = 100):
    pipeline = await get_pipeline(request)
    return JobList(jobs=[JobOut.model_validate(job) for job in pipeline.list_jobs(limit=limit)])


@app.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(request: Request, job_id: str):
    pipeline = await get_pipeline(request)
    job = pipeline.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut.model_validate(job)


@app.post("/jobs/run-once", response_model=RunOnceResponse)
async def run_once(request: Request):
    pipeline = await get_pipeline(request)
    job = await pipeline.run_once()
    return RunOnceResponse(job_id=job.job_id, status=job.status)


@app.post("/brief/refresh", response_model=BriefRefreshResponse)
async def refresh_brief(request: Request):
    pipeline = await get_pipeline(request)
    try:
        brief = await pipeline.refresh_brief_only()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return BriefRefreshResponse(brief=brief)


@app.post("/jobs/{job_id}/retry", response_model=RetryResponse)
async def retry_job(request: Request, job_id: str):
    pipeline = await get_pipeline(request)
    try:
        job = await pipeline.retry_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RetryResponse(job_id=job.job_id, status=job.status)
