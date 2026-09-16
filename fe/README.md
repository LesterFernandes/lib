# Library frontend

A Next.js interface for the library catalogue, members, and book loans.

## Development

From the `fe` directory:

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Open [localhost:3000](http://localhost:3000) for the dashboard. It links to the books and members sections.

The frontend connects to the FastAPI server at `http://localhost:8000` by default. To use another address, set `NEXT_PUBLIC_API_BASE_URL` in `.env.local`. The server's `FRONTEND_ORIGIN` must match the frontend URL.

## Checks and production build

```bash
pnpm lint
pnpm format:check
pnpm build
pnpm start
```
