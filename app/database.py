"""One session per request; rollback failed work and always close."""

from collections.abc import Iterator
from typing import Any

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def build_engine(url: str) -> Engine:
    options: dict[str, Any] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 10}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            options["poolclass"] = StaticPool
    return create_engine(url, **options)


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
