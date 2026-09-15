"""Read-only author and publisher catalogue routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Author, Publisher
from schemas import AuthorRead, PublisherRead
from services.catalog import list_authors, list_publishers

router = APIRouter(tags=["catalogue"])


@router.get("/authors", response_model=list[AuthorRead])
def list_authors_route(session: Session = Depends(get_db)) -> list[Author]:
    return list_authors(session)


@router.get("/publishers", response_model=list[PublisherRead])
def list_publishers_route(session: Session = Depends(get_db)) -> list[Publisher]:
    return list_publishers(session)
