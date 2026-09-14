"""Shared transaction helpers for synchronous SQLAlchemy services."""

from collections.abc import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.exceptions import ConflictError


def commit_or_raise_conflict(
    session: Session,
    *,
    conflict_factory: Callable[[], ConflictError],
) -> None:
    """Commit a transaction and turn constraint violations into API-safe errors."""
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise conflict_factory() from exc
