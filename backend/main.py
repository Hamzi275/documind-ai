"""DocuMind AI — FastAPI application entrypoint."""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, ingest

load_dotenv()

app = FastAPI(title="DocuMind AI")


# Manual OPTIONS catch-all, registered before CORS middleware is added.
# This avoids 400 errors on CORS preflight requests, a known issue with
# FastAPI + the Vite dev server.
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str) -> dict:
    return {}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
async def root() -> dict:
    return {"status": "ok", "service": "DocuMind AI"}
