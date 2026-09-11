from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root() -> dict[str, str]:
    """A small JSON endpoint to confirm the server is running."""
    return {"message": "Hello from FastAPI!"}

