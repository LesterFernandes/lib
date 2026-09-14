"""Loan and return business logic."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Book, Loan, Member, MemberStatus
from schemas import LoanCreate
from services.exceptions import ConflictError, NotFoundError


def _get_book(session: Session, book_id: UUID) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise NotFoundError(code="book_not_found", message="The requested book was not found.")
    return book


def _get_member(session: Session, member_id: UUID) -> Member:
    member = session.get(Member, member_id)
    if member is None:
        raise NotFoundError(code="member_not_found", message="The requested member was not found.")
    return member


def borrow_book(session: Session, payload: LoanCreate) -> Loan:
    """Record a loan, allowing only one outstanding loan per book."""
    _get_book(session, payload.book_id)
    member = _get_member(session, payload.member_id)
    if member.status is not MemberStatus.ACTIVE:
        raise ConflictError(
            code="member_not_eligible",
            message="Only active members may borrow books.",
            details={"member_status": member.status.value},
        )

    active_loan = session.scalar(
        select(Loan.id).where(Loan.book_id == payload.book_id, Loan.returned_at.is_(None))
    )
    if active_loan is not None:
        raise ConflictError(
            code="book_unavailable",
            message="This book is already on loan.",
        )

    loan = Loan(book_id=payload.book_id, member_id=payload.member_id)
    session.add(loan)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError(
            code="book_unavailable",
            message="This book is already on loan.",
        ) from exc

    session.refresh(loan)
    return loan


def return_book(session: Session, loan_id: UUID) -> Loan:
    """Close a current loan and record the return time."""
    loan = session.scalar(select(Loan).where(Loan.id == loan_id).with_for_update())
    if loan is None:
        raise NotFoundError(code="loan_not_found", message="The requested loan was not found.")
    if loan.returned_at is not None:
        raise ConflictError(
            code="loan_already_returned",
            message="This loan has already been returned.",
        )

    loan.returned_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(loan)
    return loan
