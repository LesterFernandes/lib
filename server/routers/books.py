"""Book API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import BookCreate, BookRead, BookUpdate
from services.books import create_book, update_book

router = APIRouter(prefix="/books", tags=["books"])


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book_route(payload: BookCreate, session: Session = Depends(get_db)) -> BookRead:
    return create_book(session, payload)


@router.patch("/{book_id}", response_model=BookRead)
def update_book_route(
    book_id: UUID, payload: BookUpdate, session: Session = Depends(get_db)
) -> BookRead:
    return update_book(session, book_id, payload)
