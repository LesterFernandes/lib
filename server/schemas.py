"""Pydantic request/response shapes for the future REST interface.

The schemas validate HTTP input but contain no persistence operations.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models import MemberStatus, StaffRole


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(Schema):
    id: UUID
    created_at: datetime
    updated_at: datetime


class StaffFields(Schema):
    full_name: str = Field(max_length=150)
    email: str = Field(max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    role: StaffRole = StaffRole.LIBRARIAN


class StaffCreate(StaffFields):
    """Accept plaintext only at the API boundary; hash it before persistence."""

    password: str = Field(min_length=8, max_length=128)


class StaffRead(StaffFields, TimestampedSchema):
    """Never returns password or password_hash."""

    is_active: bool


class AuthorCreate(Schema):
    full_name: str = Field(max_length=200)
    biography: str | None = None


class AuthorRead(AuthorCreate, TimestampedSchema):
    pass


class PublisherCreate(Schema):
    name: str = Field(max_length=200)
    website: str | None = Field(default=None, max_length=500)
    contact_email: str | None = Field(default=None, max_length=255)


class PublisherRead(PublisherCreate, TimestampedSchema):
    pass


class CategoryCreate(Schema):
    name: str = Field(max_length=100)
    description: str | None = None
    parent_id: UUID | None = None


class CategoryRead(CategoryCreate, TimestampedSchema):
    pass


class BookAuthorInput(Schema):
    author_id: UUID
    role: str = Field(default="author", max_length=50)
    display_order: int = Field(default=1, ge=1)


class BookCreate(Schema):
    publisher_id: UUID | None = None
    title: str = Field(max_length=500)
    subtitle: str | None = Field(default=None, max_length=500)
    description: str | None = None
    language: str = Field(default="en", max_length=10)
    authors: list[BookAuthorInput] = Field(default_factory=list)
    category_ids: list[UUID] = Field(default_factory=list)


class BookRead(BookCreate, TimestampedSchema):
    pass


class MemberCreate(Schema):
    card_number: str = Field(max_length=50)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address_line_1: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    expires_on: date | None = None
    notes: str | None = None


class MemberRead(MemberCreate, TimestampedSchema):
    joined_on: date
    status: MemberStatus
