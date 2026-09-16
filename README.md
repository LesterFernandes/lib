# Library

A library management app with a FastAPI/PostgreSQL backend and a Next.js frontend.

## Server setup

Install PostgreSQL and Python 3.12 or newer, and make sure PostgreSQL is running locally.

1. Create the database using `psql` or pgAdmin:

   ```sql
   CREATE DATABASE library;
   ```

2. Create `server/.env` with this single setting:

   ```dotenv
   DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/library
   ```

   Replace `postgres` and `YOUR_PASSWORD` with your PostgreSQL username and password.

3. Install uv and the server dependencies, starting from the repository root:

   ```bash
   python -m pip install uv
   cd server
   uv sync --locked
   ```

   This creates `server/.venv` and installs the dependencies recorded in `pyproject.toml` and `uv.lock`, including FastAPI, SQLAlchemy, Psycopg, Alembic, and Uvicorn.

4. Apply the database migrations from `server`:

   ```bash
   uv run python -m alembic upgrade head
   ```

5. Start the development server from `server`:

   ```bash
   uv run python -m uvicorn main:app --reload --env-file .env
   ```

   The API runs at [localhost:8000](http://localhost:8000). Interactive API documentation is available at [localhost:8000/docs](http://localhost:8000/docs). Leave this terminal running.

## Frontend setup

Install Node.js 20.9 or newer with npm. The project uses pnpm 8.10.0.

In a second terminal, starting from the repository root:

```bash
npm install -g pnpm@8.10.0
cd fe
pnpm install --frozen-lockfile
pnpm dev
```

Open [localhost:3000](http://localhost:3000). The frontend uses the API at `http://localhost:8000`; no frontend environment file is needed. Keep both development servers running.

## Pages and features

| Page                  | Features                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/`                   | Dashboard with links to Books and Members.                                                                                                        |
| `/books`              | Browse books, see current loans with borrower details and borrowing times, and open records for editing.                                          |
| `/books/add`          | Add a book with an optional author and publisher.                                                                                                 |
| `/books/[bookId]`     | Edit a book's details.                                                                                                                            |
| `/members`            | Browse active members and open their profiles.                                                                                                    |
| `/members/add`        | Register a member with contact and membership details.                                                                                            |
| `/members/[memberId]` | View member details and borrowing history, borrow books, and record returns. Only active members can borrow; each book can have one current loan. |

The books page uses `GET /books?include_loans=true` to highlight current loans and show borrower details. The API flag defaults to `false` for other callers.
