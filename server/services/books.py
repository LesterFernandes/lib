"""Book creation and update business logic."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Author, Book, BookAuthor, BookCategory, Category, Publisher
from schemas import BookAuthorInput, BookCreate, BookUpdate
from services.exceptions import BusinessRuleError, ConflictError, NotFoundError
from services.persistence import commit_or_raise_conflict


def _get_book(session: Session, book_id: UUID) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise NotFoundError(
            code="book_not_found",
            message="The requested book was not found.",
        )
    return book


def _validate_related_ids(
    session: Session,
    *,
    model: type[Author] | type[Category],
    ids: list[UUID],
    resource_name: str,
) -> None:
    if not ids:
        return

    missing_ids = set(ids) - set(session.scalars(select(model.id).where(model.id.in_(ids))).all())
    if missing_ids:
        raise NotFoundError(
            code=f"{resource_name}_not_found",
            message=f"One or more referenced {resource_name}s were not found.",
            details={"ids": sorted(str(item) for item in missing_ids)},
        )


def _validate_book_relationships(
    session: Session,
    *,
    publisher_id: UUID | None,
    authors: list[BookAuthorInput] | None,
    category_ids: list[UUID] | None,
) -> None:
    if publisher_id is not None and session.get(Publisher, publisher_id) is None:
        raise NotFoundError(
            code="publisher_not_found",
            message="The referenced publisher was not found.",
        )

    if authors is not None:
        author_ids = [author.author_id for author in authors]
        display_orders = [author.display_order for author in authors]
        if len(author_ids) != len(set(author_ids)):
            raise BusinessRuleError(
                code="duplicate_book_author",
                message="Each author may appear only once on a book.",
            )
        if len(display_orders) != len(set(display_orders)):
            raise BusinessRuleError(
                code="duplicate_author_display_order",
                message="Each book author must have a unique display order.",
            )
        _validate_related_ids(session, model=Author, ids=author_ids, resource_name="author")

    if category_ids is not None:
        if len(category_ids) != len(set(category_ids)):
            raise BusinessRuleError(
                code="duplicate_book_category",
                message="Each category may appear only once on a book.",
            )
        _validate_related_ids(session, model=Category, ids=category_ids, resource_name="category")


def _set_book_relationships(
    book: Book,
    *,
    authors: list[BookAuthorInput] | None,
    category_ids: list[UUID] | None,
) -> None:
    if authors is not None:
        book.author_links = [
            BookAuthor(
                author_id=author.author_id,
                role=author.role,
                display_order=author.display_order,
            )
            for author in authors
        ]
    if category_ids is not None:
        book.category_links = [BookCategory(category_id=category_id) for category_id in category_ids]


def _commit_book(session: Session, book: Book) -> Book:
    commit_or_raise_conflict(
        session,
        conflict_factory=lambda: ConflictError(
            code="book_conflict",
            message="A book with these values conflicts with existing data.",
        ),
    )
    session.refresh(book)
    return book


def create_book(session: Session, payload: BookCreate) -> Book:
    """Create one catalogue book record and its supplied associations."""
    data: dict[str, Any] = payload.model_dump()
    authors = payload.authors
    category_ids = payload.category_ids
    data.pop("authors")
    data.pop("category_ids")
    _validate_book_relationships(
        session,
        publisher_id=payload.publisher_id,
        authors=authors,
        category_ids=category_ids,
    )

    book = Book(**data)
    _set_book_relationships(book, authors=authors, category_ids=category_ids)
    session.add(book)
    return _commit_book(session, book)


def update_book(session: Session, book_id: UUID, payload: BookUpdate) -> Book:
    """Apply only fields supplied by the client to an existing book."""
    book = _get_book(session, book_id)
    data: dict[str, Any] = payload.model_dump(exclude_unset=True)
    authors = data.pop("authors", None)
    category_ids = data.pop("category_ids", None)

    _validate_book_relationships(
        session,
        publisher_id=data.get("publisher_id"),
        authors=authors if "authors" in payload.model_fields_set else None,
        category_ids=category_ids if "category_ids" in payload.model_fields_set else None,
    )

    for field, value in data.items():
        setattr(book, field, value)

    _set_book_relationships(
        book,
        authors=authors if "authors" in payload.model_fields_set else None,
        category_ids=category_ids if "category_ids" in payload.model_fields_set else None,
    )
    return _commit_book(session, book)
