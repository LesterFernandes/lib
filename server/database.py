"""Database engine and session helpers.

Set DATABASE_URL in the environment for each deployment. The default targets a
local PostgreSQL database named ``library`` and is only a development
convenience; credentials should not be committed to source code.
"""

from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/library",
)

# An engine connects lazily, when a session first performs database work.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a transaction-capable session for a future FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
