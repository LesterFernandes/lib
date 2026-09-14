"""SQLAlchemy models for the library catalogue, members, and staff.

The service represents one neighbourhood library, so it intentionally has no
branch, inventory-copy, or circulation tables. Database tables are not created
at import time; introduce migrations with Alembic when persistence is wired in.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class MemberStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    INACTIVE = "inactive"


class StaffRole(str, Enum):
    ADMIN = "admin"
    LIBRARIAN = "librarian"


def enum_values(enum_class: type[Enum]) -> list[str]:
    """Persist human-readable enum values rather than Python member names."""
    return [member.value for member in enum_class]


def library_enum(enum_class: type[Enum], name: str) -> SqlEnum:
    return SqlEnum(enum_class, name=name, values_callable=enum_values)


class UUIDPrimaryKeyMixin:
    """Technical primary key included on every main entity."""

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=text("gen_random_uuid()"))


class TimestampMixin:
    """Audit fields shared by every main entity."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Staff(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Authenticated library users.

    ``password_hash`` must contain a bcrypt/Argon2-style hash, never the
    password sent by the user. ``ADMIN`` is the management-level application
    role and ``LIBRARIAN`` is the regular staff role.
    """

    __tablename__ = "staff"

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    role: Mapped[StaffRole] = mapped_column(
        library_enum(StaffRole, "staff_role"), default=StaffRole.LIBRARIAN, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Author(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "authors"

    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    biography: Mapped[str | None] = mapped_column(Text)

    book_links: Mapped[list[BookAuthor]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


class Publisher(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publishers"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    contact_email: Mapped[str | None] = mapped_column(String(255))

    books: Mapped[list[Book]] = relationship(back_populates="publisher")


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A hierarchical catalogue category, such as Fiction > Mystery."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("name", "parent_id", name="uq_category_name_within_parent"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("categories.id"))

    parent: Mapped[Category | None] = relationship(back_populates="children", remote_side="Category.id")
    children: Mapped[list[Category]] = relationship(back_populates="parent")
    book_links: Mapped[list[BookCategory]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Book(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A catalogue record for a title.

    Aside from technical ID/audit fields, this table has only the five requested
    book columns. Author and category memberships live in link tables.
    """

    __tablename__ = "books"

    publisher_id: Mapped[UUID | None] = mapped_column(ForeignKey("publishers.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    publisher: Mapped[Publisher | None] = relationship(back_populates="books")
    author_links: Mapped[list[BookAuthor]] = relationship(
        back_populates="book", cascade="all, delete-orphan", order_by="BookAuthor.display_order"
    )
    category_links: Mapped[list[BookCategory]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    loans: Mapped[list[Loan]] = relationship(back_populates="book")

    @property
    def authors(self) -> list[BookAuthor]:
        """Serializer-friendly alias for author association objects."""
        return self.author_links

    @property
    def category_ids(self) -> list[UUID]:
        return [link.category_id for link in self.category_links]


class BookAuthor(Base):
    """Many-to-many book/author link with contributor role and display order."""

    __tablename__ = "book_authors"
    __table_args__ = (
        CheckConstraint("display_order > 0", name="ck_book_author_positive_display_order"),
        UniqueConstraint("book_id", "display_order", name="uq_book_author_display_order"),
    )

    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), default="author", nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    book: Mapped[Book] = relationship(back_populates="author_links")
    author: Mapped[Author] = relationship(back_populates="book_links")


class BookCategory(Base):
    __tablename__ = "book_categories"

    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )

    book: Mapped[Book] = relationship(back_populates="category_links")
    category: Mapped[Category] = relationship(back_populates="book_links")


class Member(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "members"

    card_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    address_line_1: Mapped[str | None] = mapped_column(String(255))
    address_line_2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    joined_on: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    expires_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[MemberStatus] = mapped_column(
        library_enum(MemberStatus, "member_status"), default=MemberStatus.ACTIVE, nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)
    loans: Mapped[list[Loan]] = relationship(back_populates="member")


class Loan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A member's loan of the library's single physical copy of a book."""

    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint(
            "returned_at IS NULL OR returned_at >= borrowed_at",
            name="ck_loan_returned_after_borrowed",
        ),
        Index(
            "uq_loans_active_book",
            "book_id",
            unique=True,
            postgresql_where=text("returned_at IS NULL"),
        ),
        Index(
            "ix_loans_active_member",
            "member_id",
            postgresql_where=text("returned_at IS NULL"),
        ),
    )

    book_id: Mapped[UUID] = mapped_column(
        ForeignKey("books.id", ondelete="RESTRICT"), nullable=False
    )
    member_id: Mapped[UUID] = mapped_column(
        ForeignKey("members.id", ondelete="RESTRICT"), nullable=False
    )
    borrowed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    book: Mapped[Book] = relationship(back_populates="loans")
    member: Mapped[Member] = relationship(back_populates="loans")


ALL_MODELS: tuple[type[Base], ...] = (
    Staff,
    Author,
    Publisher,
    Category,
    Book,
    BookAuthor,
    BookCategory,
    Member,
    Loan,
)
