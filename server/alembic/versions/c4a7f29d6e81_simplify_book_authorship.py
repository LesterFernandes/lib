"""Replace book associations with a single author foreign key.

Revision ID: c4a7f29d6e81
Revises: 8b63bca1632d

Keep each book's first author by display order. Category data and additional
authors are discarded; downgrade restores the old structure, not that data.
"""

from alembic import op
import sqlalchemy as sa


revision = "c4a7f29d6e81"
down_revision = "8b63bca1632d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("author_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_books_author_id", "books", "authors", ["author_id"], ["id"])
    op.execute(
        """
        UPDATE books
        SET author_id = (
            SELECT author_id
            FROM book_authors
            WHERE book_authors.book_id = books.id
            ORDER BY display_order
            LIMIT 1
        )
        """
    )
    op.drop_table("book_authors")
    op.drop_table("book_categories")
    op.drop_table("categories")


def downgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "parent_id", name="uq_category_name_within_parent"),
    )
    op.create_table(
        "book_categories",
        sa.Column("book_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("book_id", "category_id"),
    )
    op.create_table(
        "book_authors",
        sa.Column("book_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("book_id", "author_id"),
        sa.CheckConstraint("display_order > 0", name="ck_book_author_positive_display_order"),
        sa.UniqueConstraint("book_id", "display_order", name="uq_book_author_display_order"),
    )
    op.execute(
        """
        INSERT INTO book_authors (book_id, author_id, role, display_order)
        SELECT id, author_id, 'author', 1
        FROM books
        WHERE author_id IS NOT NULL
        """
    )
    op.drop_constraint("fk_books_author_id", "books", type_="foreignkey")
    op.drop_column("books", "author_id")
