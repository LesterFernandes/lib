"""Member list, detail, and creation API tests with an isolated database."""

from datetime import date, datetime, timezone
import unittest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import Author, Book, Loan, Member, MemberStatus, Publisher


class MemberApiTests(unittest.TestCase):
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
            self.engine,
            tables=[
                Author.__table__, Publisher.__table__, Book.__table__,
                Member.__table__, Loan.__table__,
            ],
        )

        def get_test_db():
            with Session(self.engine, autoflush=False) as session:
                yield session

        app.dependency_overrides[get_db] = get_test_db
        self.addCleanup(app.dependency_overrides.pop, get_db)
        # Skip the lifespan probe of the configured PostgreSQL database.
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def create_member(self, **changes):
        response = self.client.post(
            "/members",
            json={
                "card_number": "CARD-001",
                "first_name": "Ada",
                "last_name": "Lovelace",
                **changes,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_empty_active_member_list(self):
        response = self.client.get("/members")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_list_returns_only_active_members_and_only_requested_fields(self):
        later = self.create_member(card_number="Z-002", first_name="Zoe")
        earlier = self.create_member(email="ada@example.test", notes="Private notes")
        for status in (MemberStatus.SUSPENDED, MemberStatus.EXPIRED, MemberStatus.INACTIVE):
            self.create_member(card_number=status.value, status=status.value)

        response = self.client.get("/members")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([row["id"] for row in response.json()], [earlier["id"], later["id"]])
        for row in response.json():
            self.assertEqual(set(row), {"id", "card_number", "first_name", "last_name"})

    def test_create_with_minimal_details_uses_membership_defaults(self):
        member = self.create_member()
        self.assertEqual(member["status"], "active")
        self.assertEqual(member["joined_on"], date.today().isoformat())
        self.assertIsNone(member["email"])
        self.assertIsNone(member["expires_on"])
        detail = self.client.get(f"/members/{member['id']}")
        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertEqual(detail.json(), {**member, "loans": []})

    def test_detail_includes_all_fields_and_only_that_members_loan_history(self):
        fields = {
            "email": "ada@example.test",
            "phone": "+91 1234567890",
            "address_line_1": "10 Library Road",
            "address_line_2": "Unit 2",
            "city": "Pune",
            "postal_code": "411001",
            "date_of_birth": "1990-12-10",
            "joined_on": "2024-01-01",
            "expires_on": "2027-12-31",
            "status": "inactive",
            "notes": "Member notes\nSecond line",
        }
        member = self.create_member(**fields)
        other = self.create_member(card_number="OTHER")
        with Session(self.engine) as session:
            books = [Book(title=title) for title in ("Current book", "Returned book", "Other book")]
            session.add_all(books)
            session.flush()
            borrowed = datetime(2025, 1, 1, tzinfo=timezone.utc)
            returned = datetime(2025, 1, 5, tzinfo=timezone.utc)
            current_loan = Loan(book_id=books[0].id, member_id=UUID(member["id"]), borrowed_at=borrowed)
            returned_loan = Loan(
                book_id=books[1].id, member_id=UUID(member["id"]),
                borrowed_at=borrowed, returned_at=returned,
            )
            other_loan = Loan(book_id=books[2].id, member_id=UUID(other["id"]), borrowed_at=borrowed)
            session.add_all([current_loan, returned_loan, other_loan])
            session.commit()
            expected_ids = {str(current_loan.id), str(returned_loan.id)}

        response = self.client.get(f"/members/{member['id']}")
        self.assertEqual(response.status_code, 200, response.text)
        detail = response.json()
        for field, value in {**member, **fields}.items():
            self.assertEqual(detail[field], value, field)
        self.assertEqual({loan["id"] for loan in detail["loans"]}, expected_ids)
        self.assertEqual({loan["book"]["title"] for loan in detail["loans"]}, {"Current book", "Returned book"})
        self.assertEqual(sum(loan["returned_at"] is None for loan in detail["loans"]), 1)
        for loan in detail["loans"]:
            self.assertEqual(loan["member_id"], member["id"])
            self.assertEqual(loan["book_id"], loan["book"]["id"])
            self.assertIn("created_at", loan)
            self.assertIn("updated_at", loan)

    def test_missing_and_invalid_member_ids_keep_structured_errors(self):
        response = self.client.get(f"/members/{uuid4()}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "member_not_found")
        response = self.client.get("/members/not-a-uuid")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_create_rejects_invalid_fields_and_conflicting_card_or_email(self):
        self.create_member(email="ada@example.test")
        for changes in ({}, {"card_number": "DIFFERENT", "email": "ada@example.test"}):
            response = self.client.post(
                "/members",
                json={"card_number": "CARD-001", "first_name": "Other", "last_name": "Member", **changes},
            )
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(response.json()["error"]["code"], "member_conflict")
        for changes in ({"first_name": ""}, {"joined_on": "not-a-date"}, {"status": "unknown"}):
            response = self.client.post(
                "/members",
                json={"card_number": "VALID", "first_name": "Other", "last_name": "Member", **changes},
            )
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_existing_update_endpoint_still_updates_and_affects_active_list(self):
        member = self.create_member()
        response = self.client.patch(
            f"/members/{member['id']}", json={"status": "suspended", "phone": "12345"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["phone"], "12345")
        self.assertEqual(self.client.get("/members").json(), [])
        detail = self.client.get(f"/members/{member['id']}").json()
        self.assertEqual(detail["status"], "suspended")
        self.assertEqual(detail["loans"], [])


if __name__ == "__main__":
    unittest.main()
