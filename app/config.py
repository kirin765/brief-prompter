from functools import lru_cache
from typing import Optional, Tuple

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # External services
    openai_api_key: Optional[SecretStr] = None
    openai_model: str = "gpt-4.1-mini"
    luma_api_key: Optional[SecretStr] = None
    tiktok_client_key: Optional[SecretStr] = None
    tiktok_client_secret: Optional[SecretStr] = None
    tiktok_access_token: Optional[SecretStr] = None

    # App
    app_timezone: str = "Asia/Seoul"
    brief_file_path: str = "./data/current_brief.txt"
    database_url: str = "sqlite:///./data/brief_prompter.db"
    log_level: str = "INFO"
    luma_poll_interval_sec: int = Field(default=10, ge=1)
    luma_timeout_sec: int = Field(default=600, ge=30)
    luma_generation_endpoint: str = "https://api.lumalabs.ai/dream-machine/v1/generations"
    luma_status_endpoint: str = "https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}"
    luma_model: str = "ray-2"
    luma_resolution: str = "720p"
    luma_duration: str = "15s"
    tiktok_api_base: str = "https://open.tiktokapis.com"
    tiktok_upload_endpoint: str = "/v2/video/upload/"
    tiktok_publish_endpoint: str = "/v2/video/post/"

    # Reliability
    max_retries: int = Field(default=3, ge=0)
    retry_initial_delay: float = Field(default=1.0, gt=0)
    retry_max_delay: float = Field(default=30.0, gt=0)
    max_concurrent_runs: int = Field(default=1, ge=1)

    # Runtime controls
    dry_run: bool = False
    enable_scheduler: bool = True
    caption_language: str = "ko"
    caption_length_limit: int = Field(default=80, ge=12)
    http_timeout_sec: int = Field(default=30, ge=1)
    run_on_startup: bool = False

    # Internal helper
    schedule_hours: list[int] = Field(default=[0, 6, 12, 18])

    # Legacy compatibility
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _to_int_tuple(schedule: list[int]) -> Tuple[int, ...]:
    return tuple(
        int(hour)
        for hour in schedule
        if 0 <= int(hour) <= 23
    )


def schedule_expression(settings: Settings) -> str:
    return ",".join(str(hour) for hour in _to_int_tuple(settings.schedule_hours))
