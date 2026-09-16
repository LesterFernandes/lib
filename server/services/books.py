"""Book lookup, creation, and update business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, load_only

from models import Author, Book, Publisher
from schemas import BookCreate, BookUpdate
from services.exceptions import NotFoundError


def list_books(session: Session) -> list[Book]:
    """Return all books ordered by title, loading only list fields."""
    return list(
        session.scalars(
            select(Book)
            .options(load_only(Book.id, Book.title, Book.author_id, Book.publisher_id))
            .order_by(Book.title, Book.id)
        )
    )


def get_book(session: Session, book_id: UUID) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise NotFoundError(
            code="book_not_found",
            message="The requested book was not found.",
        )
    return book


def _validate_book_references(
    session: Session, payload: BookCreate | BookUpdate
) -> None:
    if payload.author_id is not None and session.get(Author, payload.author_id) is None:
        raise NotFoundError(
            code="author_not_found",
            message="The referenced author was not found.",
        )
    if payload.publisher_id is not None and session.get(Publisher, payload.publisher_id) is None:
        raise NotFoundError(
            code="publisher_not_found",
            message="The referenced publisher was not found.",
        )


def _commit_book(session: Session, book: Book) -> Book:
    session.commit()
    session.refresh(book)
    return book


def create_book(session: Session, payload: BookCreate) -> Book:
    """Create one catalogue book record."""
    _validate_book_references(session, payload)
    book = Book(**payload.model_dump())
    session.add(book)
    return _commit_book(session, book)


def update_book(session: Session, book_id: UUID, payload: BookUpdate) -> Book:
    """Apply only fields supplied by the client to an existing book."""
    book = get_book(session, book_id)
    _validate_book_references(session, payload)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    return _commit_book(session, book)
