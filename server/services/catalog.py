from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Author, Publisher


def list_authors(session: Session) -> list[Author]:
    return list(session.scalars(select(Author).order_by(Author.full_name)))


def list_publishers(session: Session) -> list[Publisher]:
    return list(session.scalars(select(Publisher).order_by(Publisher.name)))
