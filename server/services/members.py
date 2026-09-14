"""Member creation and update business logic."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from models import Member
from schemas import MemberCreate, MemberUpdate
from services.exceptions import ConflictError, NotFoundError
from services.persistence import commit_or_raise_conflict


def _get_member(session: Session, member_id: UUID) -> Member:
    member = session.get(Member, member_id)
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
    member = _get_member(session, member_id)
    data: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(member, field, value)
    return _commit_member(session, member)
