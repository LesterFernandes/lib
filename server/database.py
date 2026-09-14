"""Database engine and session helpers.

Set DATABASE_URL in the environment for each deployment. The default targets a
local PostgreSQL database named ``library`` and is only a development
convenience; credentials should not be committed to source code.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings

# An engine connects lazily, when a session first performs database work.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    """Yield a transaction-capable session for a future FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
