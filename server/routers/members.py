"""Member API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models import Member
from schemas import MemberCreate, MemberDetailRead, MemberListItem, MemberRead, MemberUpdate
from services.members import create_member, get_member, list_active_members, update_member

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=list[MemberListItem])
def list_members_route(session: Session = Depends(get_db)) -> list[Member]:
    return list_active_members(session)


@router.post("", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_member_route(payload: MemberCreate, session: Session = Depends(get_db)) -> Member:
    return create_member(session, payload)


@router.get("/{member_id}", response_model=MemberDetailRead)
def get_member_route(member_id: UUID, session: Session = Depends(get_db)) -> Member:
    return get_member(session, member_id)


@router.patch("/{member_id}", response_model=MemberRead)
def update_member_route(
    member_id: UUID, payload: MemberUpdate, session: Session = Depends(get_db)
) -> Member:
    return update_member(session, member_id, payload)
