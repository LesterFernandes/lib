"""Member lookup, creation, and update business logic."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, load_only, selectinload

from models import Book, Loan, Member, MemberStatus
from schemas import MemberCreate, MemberUpdate
from services.exceptions import ConflictError, NotFoundError
from services.persistence import commit_or_raise_conflict


def list_active_members(session: Session) -> list[Member]:
    """Return active members alphabetically, loading only list fields."""
    return list(
        session.scalars(
            select(Member)
            .where(Member.status == MemberStatus.ACTIVE)
            .options(load_only(Member.id, Member.card_number, Member.first_name, Member.last_name))
            .order_by(Member.first_name, Member.last_name, Member.card_number)
        )
    )


def get_member(session: Session, member_id: UUID) -> Member:
    """Return one member with their complete loan history and loaned books."""
    member = session.scalar(
        select(Member)
        .where(Member.id == member_id)
        .options(
            selectinload(Member.loans).joinedload(Loan.book).load_only(Book.id, Book.title)
        )
    )
    if member is None:
        raise NotFoundError(
            code="member_not_found",
            message="The requested member was not found.",
        )
    return member


def _commit_member(session: Session, member: Member) -> Member:
    commit_or_raise_conflict(
        session,
        conflict_factory=lambda: ConflictError(
            code="member_conflict",
            message="A member with this card number or email already exists.",
        ),
    )
    session.refresh(member)
    return member


def create_member(session: Session, payload: MemberCreate) -> Member:
    """Create a library member."""
    member = Member(**payload.model_dump())
    session.add(member)
    return _commit_member(session, member)


def update_member(session: Session, member_id: UUID, payload: MemberUpdate) -> Member:
    """Apply only fields supplied by the client to an existing member."""
    member = get_member(session, member_id)
    data: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(member, field, value)
    return _commit_member(session, member)
