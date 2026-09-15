"""Read-only catalogue lookup operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Author, Publisher


def list_authors(session: Session) -> list[Author]:
    """Return authors alphabetically for book-entry selection."""
    return list(session.scalars(select(Author).order_by(Author.full_name)))


def list_publishers(session: Session) -> list[Publisher]:
    """Return publishers alphabetically for book-entry selection."""
    return list(session.scalars(select(Publisher).order_by(Publisher.name)))
