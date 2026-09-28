import os
from pathlib import Path
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        if configured.startswith("postgres://"):
            return configured.replace("postgres://", "postgresql+psycopg://", 1)
        if configured.startswith("postgresql://"):
            return configured.replace("postgresql://", "postgresql+psycopg://", 1)
        return configured
    return f"sqlite:///{os.getenv('DATABASE_PATH', 'data/diet_planner.db')}"


def make_engine(url: str | None = None):
    resolved = make_url(url or database_url())
    if resolved.drivername.startswith("sqlite") and resolved.database not in (None, ":memory:"):
        Path(resolved.database).parent.mkdir(parents=True, exist_ok=True)
    options = {"check_same_thread": False} if resolved.drivername.startswith("sqlite") else {}
    return create_engine(resolved, connect_args=options, pool_pre_ping=True)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()