"""One session per request; rollback failed work and always close."""
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def build_engine(url: str):
    options = {'pool_pre_ping': True}
    if url.startswith('sqlite'):
        options['connect_args'] = {'check_same_thread': False, 'timeout': 10}
        if url in {'sqlite://', 'sqlite:///:memory:'}:
            options['poolclass'] = StaticPool
    return create_engine(url, **options)


def get_session(request: Request):
    with Session(request.app.state.engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
