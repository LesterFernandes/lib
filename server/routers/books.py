from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Book
from schemas import BookCreate, BookListItem, BookListItemWithLoans, BookRead, BookUpdate
from services.books import create_book, get_book, list_books, update_book

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookListItemWithLoans | BookListItem])
def list_books_route(
    include_loans: bool = Query(
        False, description="Include current loans and borrower details."
    ),
    session: Session = Depends(get_db),
) -> list[BookListItemWithLoans | BookListItem]:
    books = list_books(session, include_loans=include_loans)
    response_schema = BookListItemWithLoans if include_loans else BookListItem
    return [response_schema.model_validate(book) for book in books]


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book_route(payload: BookCreate, session: Session = Depends(get_db)) -> Book:
    return create_book(session, payload)


@router.get("/{book_id}", response_model=BookRead)
def get_book_route(book_id: UUID, session: Session = Depends(get_db)) -> Book:
    return get_book(session, book_id)


@router.patch("/{book_id}", response_model=BookRead)
def update_book_route(
    book_id: UUID, payload: BookUpdate, session: Session = Depends(get_db)
) -> Book:
    return update_book(session, book_id, payload)
