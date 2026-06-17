"""Pydantic v2 models shared across the DocuMind AI backend."""

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str
    type: str  # "pdf" | "url" | "youtube"
    title: str
    chunk_count: int
    added_at: str


class IngestResponse(BaseModel):
    source: Source
    message: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_history: list[ChatMessage] = Field(default_factory=list)


class Citation(BaseModel):
    source_id: str
    source_title: str
    source_type: str
    chunk_text: str


class UrlIngestRequest(BaseModel):
    url: str


class YoutubeIngestRequest(BaseModel):
    url: str
