import asyncio
from pathlib import Path

from app.config import Settings
from app.db.models import JobStatus
from app.db.session import init_db
from app.services.pipeline import PipelineService


class DummyBriefSource:
    async def fetch_latest(self):
        return "a sample brief"


class DummyTransformer:
    async def transform(self, brief: str):
        return "short prompt"


class DummyGenerator:
    def __init__(self, output_path: Path):
        self.output_path = output_path

    async def generate(self, prompt: str, metadata: dict = None):
        class Result:
            generation_id = "gid"
            status = "completed"
            asset_url = "http://example.com/video.mp4"
            local_video_path = ""
            status_history = []

        result = Result()
        result.local_video_path = str(self.output_path)
        return result


class DummyUploader:
    async def upload(self, video_path: str, caption: str):
        class Result:
            upload_status = "uploaded"
            success = True
            post_id = "post123"
            post_url = None
            error_message = None

        return Result()


class DummyCaption:
    async def generate_caption(self, brief: str, transformed_prompt: str) -> str:
        return "caption"


def test_pipeline_runs_one_job(tmp_path):
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    settings = Settings(database_url=db_url, luma_api_key=None, tiktok_access_token=None)
    init_db(db_url)
    video_path = tmp_path / "output" / "test.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(b"video")

    service = PipelineService(
        settings=settings,
        brief_source=DummyBriefSource(),
        prompt_transformer=DummyTransformer(),
        video_generator=DummyGenerator(video_path),
        uploader=DummyUploader(),
        caption_service=DummyCaption(),
    )

    async def run():
        job = await service.run_once()
        assert job.status == JobStatus.UPLOADED
        assert job.tiktok_post_id == "post123"

    asyncio.run(run())

    all_jobs = service.list_jobs(limit=10)
    assert len(all_jobs) == 1
    assert all_jobs[0].status == JobStatus.UPLOADED
