from collections.abc import Generator, Callable
from contextlib import contextmanager
from functools import lru_cache
from typing import Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import Settings, get_settings
from .base import Base
from .models import Job


def _engine_kwargs(database_url: str) -> dict:
    kwargs: dict[str, object] = {"echo": False, "future": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


@lru_cache

def get_engine(database_url: str) -> Engine:
    settings = get_settings()
    return create_engine(database_url or settings.database_url, **_engine_kwargs(database_url or settings.database_url))


@lru_cache
def get_session_factory(database_url: str | None = None) -> Callable[[], Session]:
    cfg = get_settings()
    database_url_final = database_url or cfg.database_url
    engine = get_engine(database_url_final)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)



def init_db(database_url: str | None = None) -> None:
    engine = get_engine(database_url or get_settings().database_url)
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope(database_url: str | None = None) -> Generator[Session, None, None]:
    factory = get_session_factory(database_url)
    session = factory()
    try:
        yield session
    finally:
        session.close()
