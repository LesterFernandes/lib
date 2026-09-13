.PHONY: install run check

# Install the exact dependency set recorded in uv.lock.
install:
	uv sync

# Start the development server with automatic reloads.
run:
	uv run python -m uvicorn main:app --reload

# Catch Python syntax/import errors without needing a running PostgreSQL server.
check:
	uv run python -m compileall -q main.py database.py models.py schemas.py
