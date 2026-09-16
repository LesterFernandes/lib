"""Book API regression tests using an isolated in-memory database."""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import Author, Book, Publisher


class BookApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.addCleanup(self.engine.dispose)

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(
            self.engine, tables=[Author.__table__, Publisher.__table__, Book.__table__]
        )
        with Session(self.engine) as session:
            first = Author(full_name="First author")
            second = Author(full_name="Second author")
            publisher = Publisher(name="Test publisher")
            session.add_all([first, second, publisher])
            session.commit()
            self.first_id = str(first.id)
            self.second_id = str(second.id)
            self.publisher_id = str(publisher.id)

        def get_test_db():
            with Session(self.engine, autoflush=False) as session:
                yield session

        app.dependency_overrides[get_db] = get_test_db
        self.addCleanup(app.dependency_overrides.pop, get_db)
        # No lifespan context: the app's startup probes the configured PostgreSQL DB.
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def create_book(self, **changes):
        response = self.client.post(
            "/books",
            json={
                "title": "A book",
                "author_id": self.first_id,
                "publisher_id": self.publisher_id,
                **changes,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_create_get_and_update_use_a_single_author(self):
        book = self.create_book()
        self.assertEqual(book["author_id"], self.first_id)
        self.assertEqual(book["publisher_id"], self.publisher_id)
        self.assertNotIn("authors", book)
        self.assertNotIn("category_ids", book)
        self.assertIn("created_at", book)
        path = f"/books/{book['id']}"
        self.assertEqual(self.client.get(path).json(), book)

        response = self.client.patch(path, json={"author_id": self.second_id})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["author_id"], self.second_id)
        self.assertEqual(response.json()["title"], book["title"])
        self.assertEqual(response.json()["publisher_id"], self.publisher_id)
        self.assertEqual(self.client.get(path).json()["author_id"], self.second_id)

    def test_empty_book_list(self):
        response = self.client.get("/books")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_book_list_returns_only_requested_fields_in_title_order(self):
        later = self.create_book(title="Zebra", description="Full description")
        earlier = self.create_book(title="Apple", author_id=None, publisher_id=None)
        response = self.client.get("/books")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            response.json(),
            [
                {"id": earlier["id"], "title": "Apple", "author_id": None, "publisher_id": None},
                {"id": later["id"], "title": "Zebra", "author_id": self.first_id, "publisher_id": self.publisher_id},
            ],
        )

        update = self.client.patch(
            f"/books/{later['id']}", json={"title": "Aardvark", "author_id": self.second_id}
        )
        self.assertEqual(update.status_code, 200, update.text)
        updated_list = self.client.get("/books").json()
        self.assertEqual(updated_list[0]["id"], later["id"])
        self.assertEqual(updated_list[0]["title"], "Aardvark")
        self.assertEqual(updated_list[0]["author_id"], self.second_id)

    def test_partial_update_preserves_omitted_references_and_null_clears_them(self):
        book = self.create_book()
        path = f"/books/{book['id']}"
        response = self.client.patch(path, json={"title": "Renamed"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["author_id"], self.first_id)
        self.assertEqual(response.json()["publisher_id"], self.publisher_id)

        response = self.client.patch(path, json={"author_id": None, "publisher_id": None})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["author_id"])
        self.assertIsNone(response.json()["publisher_id"])
        self.assertEqual(response.json()["title"], "Renamed")
        self.assertIsNone(self.client.get(path).json()["author_id"])

    def test_author_and_publisher_are_optional(self):
        response = self.client.post("/books", json={"title": "Unattributed"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertIsNone(response.json()["author_id"])
        self.assertIsNone(response.json()["publisher_id"])

    def test_duplicate_book_details_are_allowed(self):
        first = self.create_book()
        second = self.create_book()
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(
            {book["id"] for book in self.client.get("/books").json()},
            {first["id"], second["id"]},
        )

    def test_missing_references_keep_structured_errors(self):
        book = self.create_book()
        for field, code in (("author_id", "author_not_found"), ("publisher_id", "publisher_not_found")):
            for method in ("post", "patch"):
                with self.subTest(field=field, method=method):
                    path = "/books" if method == "post" else f"/books/{book['id']}"
                    response = self.client.request(method, path, json={"title": "Invalid", field: str(uuid4())})
                    self.assertEqual(response.status_code, 404, response.text)
                    self.assertEqual(response.json()["error"]["code"], code)
        self.assertEqual(self.client.get(f"/books/{book['id']}").json()["title"], book["title"])

    def test_removed_fields_and_invalid_author_ids_are_rejected(self):
        book = self.create_book()
        for changes in ({"authors": []}, {"category_ids": []}, {"author_id": "invalid"}, {"author_id": [self.first_id]}):
            for method in ("post", "patch"):
                with self.subTest(changes=changes, method=method):
                    path = "/books" if method == "post" else f"/books/{book['id']}"
                    response = self.client.request(method, path, json={"title": "Invalid", **changes})
                    self.assertEqual(response.status_code, 422, response.text)
                    self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_empty_patch_and_missing_books_keep_structured_errors(self):
        book = self.create_book()
        response = self.client.patch(f"/books/{book['id']}", json={})
        self.assertEqual(response.status_code, 422)
        for method in ("get", "patch"):
            response = self.client.request(method, f"/books/{uuid4()}", json={"title": "Missing"})
            self.assertEqual(response.status_code, 404, response.text)
            self.assertEqual(response.json()["error"]["code"], "book_not_found")

    def test_catalogue_and_openapi_expose_the_simplified_contract(self):
        self.assertEqual(
            [author["id"] for author in self.client.get("/authors").json()],
            [self.first_id, self.second_id],
        )
        self.assertEqual(self.client.get("/publishers").json()[0]["id"], self.publisher_id)
        schemas = self.client.get("/openapi.json").json()["components"]["schemas"]
        for name in ("BookCreate", "BookRead", "BookUpdate"):
            self.assertIn("author_id", schemas[name]["properties"])
            self.assertNotIn("authors", schemas[name]["properties"])
            self.assertNotIn("category_ids", schemas[name]["properties"])
        self.assertNotIn("BookAuthorInput", schemas)
        self.assertFalse({"categories", "book_categories", "book_authors"} & Base.metadata.tables.keys())


if __name__ == "__main__":
    unittest.main()
