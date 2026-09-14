"""Loan API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import LoanCreate, LoanRead
from services.loans import borrow_book, return_book

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def borrow_book_route(payload: LoanCreate, session: Session = Depends(get_db)) -> LoanRead:
    return borrow_book(session, payload)


@router.post("/{loan_id}/return", response_model=LoanRead)
def return_book_route(loan_id: UUID, session: Session = Depends(get_db)) -> LoanRead:
    return return_book(session, loan_id)
