.PHONY: install run check test migrations migrate downgrade current history check-migrations

MSG ?= migration
REVISION ?= -1
# 
# Install the exact dependency set recorded in uv.lock.
install:
	uv sync

# Start the development server with automatic reloads.
run:
	uv run python -m uvicorn main:app --reload --env-file .env

# Catch Python syntax/import errors without needing a running PostgreSQL server.
check:
	uv run python -m compileall -q main.py database.py models.py schemas.py routers services

test:
	uv run python -m unittest discover -s tests -v

# migration related scripts
migrations:
	uv run python -m alembic revision --autogenerate -m "$(MSG)"

migrate:
	uv run python -m alembic upgrade head

downgrade:
	uv run python -m alembic downgrade $(REVISION)

current:
	uv run python -m alembic current

history:
	uv run python -m alembic history

check-migrations:
	uv run python -m alembic check
