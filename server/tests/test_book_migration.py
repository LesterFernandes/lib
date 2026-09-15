"""PostgreSQL migration coverage in a temporary schema rolled back after testing.

Set TEST_DATABASE_URL to a PostgreSQL database where the test user can create
schemas. Existing tables and data are not changed.
"""

import os
from pathlib import Path
import unittest
from uuid import uuid4

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Set TEST_DATABASE_URL for PostgreSQL migration tests")
class BookMigrationTests(unittest.TestCase):
    def test_upgrade_keeps_first_author_and_downgrade_restores_structure(self):
        engine = create_engine(os.environ["TEST_DATABASE_URL"])
        self.addCleanup(engine.dispose)
        connection = engine.connect()
        self.addCleanup(connection.close)
        transaction = connection.begin()
        self.addCleanup(transaction.rollback)
        schema = f"book_migration_test_{uuid4().hex}"
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')

        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        scripts = ScriptDirectory.from_config(config)
        migration = scripts.get_revision("c4a7f29d6e81").module
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            for revision in reversed(list(scripts.walk_revisions(base="base", head=migration.down_revision))):
                revision.module.upgrade()

            first, second = connection.execute(text("SELECT id FROM authors ORDER BY full_name LIMIT 2")).scalars().all()
            multiple_book, single_book, no_author_book = uuid4(), uuid4(), uuid4()
            connection.execute(
                text("INSERT INTO books (id, title, language) VALUES (:id, :title, 'en')"),
                [
                    {"id": multiple_book, "title": "Multiple authors"},
                    {"id": single_book, "title": "Single author"},
                    {"id": no_author_book, "title": "No author"},
                ],
            )
            connection.execute(
                text("INSERT INTO book_authors (book_id, author_id, role, display_order) VALUES (:book, :author, 'editor', :position)"),
                [
                    {"book": multiple_book, "author": second, "position": 7},
                    {"book": multiple_book, "author": first, "position": 2},
                    {"book": single_book, "author": second, "position": 3},
                ],
            )
            category_id = connection.execute(text("INSERT INTO categories (name) VALUES ('Old category') RETURNING id")).scalar_one()
            connection.execute(
                text("INSERT INTO book_categories (book_id, category_id) VALUES (:book, :category)"),
                {"book": multiple_book, "category": category_id},
            )

            migration.upgrade()
            self.assertFalse(
                {"categories", "book_categories", "book_authors"}
                & set(inspect(connection).get_table_names(schema=schema))
            )
            expected = {multiple_book: first, single_book: second, no_author_book: None}
            self.assertEqual(dict(connection.execute(text("SELECT id, author_id FROM books")).all()), expected)
            foreign_keys = inspect(connection).get_foreign_keys("books", schema=schema)
            self.assertTrue(any(key["constrained_columns"] == ["author_id"] and key["referred_table"] == "authors" for key in foreign_keys))

            migration.downgrade()
            self.assertNotIn("author_id", {column["name"] for column in inspect(connection).get_columns("books", schema=schema)})
            self.assertEqual(
                set(connection.execute(text("SELECT book_id, author_id, role, display_order FROM book_authors")).all()),
                {(multiple_book, first, "author", 1), (single_book, second, "author", 1)},
            )
            self.assertEqual(connection.execute(text("SELECT count(*) FROM categories")).scalar_one(), 0)
            self.assertEqual(connection.execute(text("SELECT count(*) FROM book_categories")).scalar_one(), 0)

            migration.upgrade()
            self.assertEqual(dict(connection.execute(text("SELECT id, author_id FROM books")).all()), expected)


if __name__ == "__main__":
    unittest.main()
