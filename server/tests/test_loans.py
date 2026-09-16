"""Loan API tests against PostgreSQL, including its active-loan partial index.

Set TEST_DATABASE_URL to run. Each test uses a temporary schema inside a
transaction that is rolled back, preserving the database's existing data.
"""

import os
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, get_db
from main import app
from models import Book, Member, MemberStatus
from schemas import LoanCreate
from services.exceptions import ConflictError
from services.loans import borrow_book


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Set TEST_DATABASE_URL for PostgreSQL loan tests")
class LoanApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(os.environ["TEST_DATABASE_URL"])
        self.addCleanup(self.engine.dispose)
        self.connection = self.engine.connect()
        self.addCleanup(self.connection.close)
        transaction = self.connection.begin()
        self.addCleanup(transaction.rollback)
        schema = f"loan_test_{uuid4().hex}"
        self.connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        self.connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
        Base.metadata.create_all(self.connection)

        with self.session() as session:
            book = Book(title="Borrowable book")
            member = Member(card_number="BORROWER", first_name="Ada", last_name="Lovelace")
            other = Member(card_number="OTHER", first_name="Grace", last_name="Hopper")
            session.add_all([book, member, other])
            session.commit()
            self.book_id = str(book.id)
            self.member_id = str(member.id)
            self.other_id = str(other.id)

        def get_test_db():
            with self.session() as session:
                yield session

        app.dependency_overrides[get_db] = get_test_db
        self.addCleanup(app.dependency_overrides.pop, get_db)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def session(self):
        return Session(
            self.connection, autoflush=False, join_transaction_mode="create_savepoint"
        )

    def borrow(self, **changes):
        return self.client.post(
            "/loans",
            json={"book_id": self.book_id, "member_id": self.member_id, **changes},
        )

    def test_borrow_return_and_borrow_again_preserves_history(self):
        response = self.borrow()
        self.assertEqual(response.status_code, 201, response.text)
        loan = response.json()
        self.assertEqual(loan["book_id"], self.book_id)
        self.assertEqual(loan["member_id"], self.member_id)
        self.assertIsNone(loan["returned_at"])
        detail = self.client.get(f"/members/{self.member_id}").json()
        self.assertEqual(detail["loans"][0]["book"], {"id": self.book_id, "title": "Borrowable book"})

        returned = self.client.post(f"/loans/{loan['id']}/return")
        self.assertEqual(returned.status_code, 200, returned.text)
        self.assertIsNotNone(returned.json()["returned_at"])
        self.assertEqual(returned.json()["borrowed_at"], loan["borrowed_at"])

        borrowed_again = self.borrow()
        self.assertEqual(borrowed_again.status_code, 201, borrowed_again.text)
        self.assertNotEqual(borrowed_again.json()["id"], loan["id"])
        history = self.client.get(f"/members/{self.member_id}").json()["loans"]
        self.assertEqual(len(history), 2)
        self.assertEqual(sum(item["returned_at"] is None for item in history), 1)

    def test_already_borrowed_book_is_unavailable_to_any_member(self):
        self.assertEqual(self.borrow().status_code, 201)
        for member_id in (self.member_id, self.other_id):
            response = self.borrow(member_id=member_id)
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(response.json()["error"]["code"], "book_unavailable")

    def test_only_active_members_can_borrow(self):
        for status in (MemberStatus.INACTIVE, MemberStatus.SUSPENDED, MemberStatus.EXPIRED):
            with self.session() as session:
                member = session.get(Member, UUID(self.member_id))
                member.status = status
                session.commit()
            response = self.borrow()
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(response.json()["error"]["code"], "member_not_eligible")

    def test_returns_are_allowed_after_member_becomes_inactive(self):
        loan = self.borrow().json()
        self.client.patch(f"/members/{self.member_id}", json={"status": "inactive"})
        response = self.client.post(f"/loans/{loan['id']}/return")
        self.assertEqual(response.status_code, 200, response.text)

    def test_returning_twice_keeps_original_return_time(self):
        loan = self.borrow().json()
        first = self.client.post(f"/loans/{loan['id']}/return").json()
        response = self.client.post(f"/loans/{loan['id']}/return")
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()["error"]["code"], "loan_already_returned")
        history = self.client.get(f"/members/{self.member_id}").json()["loans"]
        self.assertEqual(history[0]["returned_at"], first["returned_at"])

    def test_missing_and_invalid_ids_keep_structured_errors(self):
        for field, code in (("book_id", "book_not_found"), ("member_id", "member_not_found")):
            response = self.borrow(**{field: str(uuid4())})
            self.assertEqual(response.status_code, 404, response.text)
            self.assertEqual(response.json()["error"]["code"], code)
            response = self.borrow(**{field: "invalid"})
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(response.json()["error"]["code"], "validation_error")
        response = self.client.post(f"/loans/{uuid4()}/return")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "loan_not_found")

    def test_unique_index_handles_a_loan_created_after_the_availability_check(self):
        self.assertEqual(self.borrow().status_code, 201)
        with self.session() as session:
            # Simulate the availability check racing with another successful borrower.
            with patch.object(session, "scalar", return_value=None):
                with self.assertRaises(ConflictError) as caught:
                    borrow_book(session, LoanCreate(book_id=self.book_id, member_id=self.other_id))
            self.assertEqual(caught.exception.code, "book_unavailable")

    def test_unrelated_integrity_errors_are_not_reported_as_book_unavailable(self):
        with self.session() as session:
            add = session.add

            def delete_book_before_insert(loan):
                # A deleted reference produces a foreign-key violation, not a duplicate loan.
                session.execute(delete(Book).where(Book.id == UUID(self.book_id)))
                add(loan)

            with patch.object(session, "add", side_effect=delete_book_before_insert):
                with self.assertRaises(IntegrityError):
                    borrow_book(session, LoanCreate(book_id=self.book_id, member_id=self.member_id))


if __name__ == "__main__":
    unittest.main()
