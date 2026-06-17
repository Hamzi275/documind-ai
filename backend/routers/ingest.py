"""Ingestion endpoints: PDF upload, URL scrape, YouTube transcript."""

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import IngestResponse, Source, UrlIngestRequest, YoutubeIngestRequest
from services.chunker import chunk_text
from services.pdf_extractor import extract_pdf_text
from services.vector_store import vector_store
from services.web_scraper import scrape_url
from services.youtube_extractor import extract_youtube_transcript

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug[:max_len] or "source"


def _make_source_id(seed: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"{_slugify(seed)}-{timestamp}-{uuid.uuid4().hex[:6]}"


@router.post("/pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)) -> IngestResponse:
    try:
        file_bytes = await file.read()
        text = extract_pdf_text(file_bytes, file.filename or "uploaded.pdf")
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("No usable text could be extracted from this PDF.")

        source_id = _make_source_id(file.filename or "pdf")
        title = file.filename or "Untitled PDF"
        chunk_count = vector_store.add_source(source_id, title, "pdf", chunks)

        source = Source(
            id=source_id,
            type="pdf",
            title=title,
            chunk_count=chunk_count,
            added_at=datetime.now(timezone.utc).isoformat(),
        )
        return IngestResponse(
            source=source, message=f"Ingested '{title}' ({chunk_count} chunks)."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.post("/url", response_model=IngestResponse)
async def ingest_url(payload: UrlIngestRequest) -> IngestResponse:
    try:
        title, text = scrape_url(payload.url)
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("No usable text could be extracted from this URL.")

        source_id = _make_source_id(title or payload.url)
        chunk_count = vector_store.add_source(source_id, title, "url", chunks)

        source = Source(
            id=source_id,
            type="url",
            title=title,
            chunk_count=chunk_count,
            added_at=datetime.now(timezone.utc).isoformat(),
        )
        return IngestResponse(
            source=source, message=f"Ingested '{title}' ({chunk_count} chunks)."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.post("/youtube", response_model=IngestResponse)
async def ingest_youtube(payload: YoutubeIngestRequest) -> IngestResponse:
    try:
        video_id, transcript_text = extract_youtube_transcript(payload.url)
        chunks = chunk_text(transcript_text)
        if not chunks:
            raise ValueError("No usable transcript text was found for this video.")

        title = f"YouTube: {video_id}"
        source_id = _make_source_id(video_id)
        chunk_count = vector_store.add_source(source_id, title, "youtube", chunks)

        source = Source(
            id=source_id,
            type="youtube",
            title=title,
            chunk_count=chunk_count,
            added_at=datetime.now(timezone.utc).isoformat(),
        )
        return IngestResponse(
            source=source, message=f"Ingested '{title}' ({chunk_count} chunks)."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.get("/sources")
async def get_sources() -> list[dict]:
    return vector_store.list_sources()
