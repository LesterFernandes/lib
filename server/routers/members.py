"""Member API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import MemberCreate, MemberRead, MemberUpdate
from services.members import create_member, update_member

router = APIRouter(prefix="/members", tags=["members"])


@router.post("", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_member_route(payload: MemberCreate, session: Session = Depends(get_db)) -> MemberRead:
    return create_member(session, payload)


@router.patch("/{member_id}", response_model=MemberRead)
def update_member_route(
    member_id: UUID, payload: MemberUpdate, session: Session = Depends(get_db)
) -> MemberRead:
    return update_member(session, member_id, payload)
