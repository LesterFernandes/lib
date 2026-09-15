"""Pydantic request/response shapes for the future REST interface.

The schemas validate HTTP input but contain no persistence operations.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class AuthorRead(AuthorCreate):
    id: UUID


class PublisherCreate(Schema):
    name: str = Field(max_length=200)
    website: str | None = Field(default=None, max_length=500)
    contact_email: str | None = Field(default=None, max_length=255)


class PublisherRead(PublisherCreate):
    id: UUID


class BookCreate(Schema):
    model_config = ConfigDict(extra="forbid")

    author_id: UUID | None = None
    publisher_id: UUID | None = None
    title: str = Field(min_length=1, max_length=500)
    subtitle: str | None = Field(default=None, max_length=500)
    description: str | None = None
    language: str = Field(default="en", max_length=10)


class BookRead(BookCreate, TimestampedSchema):
    pass


class BookSummary(Schema):
    id: UUID
    title: str


class BookUpdate(Schema):
    model_config = ConfigDict(extra="forbid")

    author_id: UUID | None = None
    publisher_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    subtitle: str | None = Field(default=None, max_length=500)
    description: str | None = None
    language: str | None = Field(default=None, min_length=1, max_length=10)

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> BookUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for an update.")
        return self


class MemberCreate(Schema):
    card_number: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address_line_1: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    joined_on: date = Field(default_factory=date.today)
    expires_on: date | None = None
    status: MemberStatus = MemberStatus.ACTIVE
    notes: str | None = None


class MemberRead(MemberCreate, TimestampedSchema):
    pass


class MemberListItem(Schema):
    id: UUID
    card_number: str
    first_name: str
    last_name: str


class MemberUpdate(Schema):
    card_number: str | None = Field(default=None, min_length=1, max_length=50)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address_line_1: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    expires_on: date | None = None
    status: MemberStatus | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> MemberUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for an update.")
        return self


class LoanCreate(Schema):
    book_id: UUID
    member_id: UUID


class LoanRead(TimestampedSchema):
    book_id: UUID
    member_id: UUID
    borrowed_at: datetime
    returned_at: datetime | None


class MemberLoanRead(LoanRead):
    book: BookSummary


class MemberDetailRead(MemberRead):
    loans: list[MemberLoanRead]
