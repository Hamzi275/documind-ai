"""Streaming chat endpoint: retrieves context, streams a Groq completion."""

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.schemas import ChatRequest
from services.groq_client import stream_chat_response
from services.vector_store import vector_store

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest) -> StreamingResponse:
    retrieved_chunks = vector_store.query(request.message, top_k=5)

    citations = [
        {
            "source_id": chunk["source_id"],
            "source_title": chunk["source_title"],
            "source_type": chunk["source_type"],
            "chunk_text": chunk["chunk_text"],
        }
        for chunk in retrieved_chunks
    ]

    chat_history = [turn.model_dump() for turn in request.chat_history]

    async def event_stream():
        # Sent first so the frontend can render citation chips before, or
        # while, the answer is still streaming in.
        yield f"data: __CITATIONS__{json.dumps(citations)}\n\n"
        async for token_event in stream_chat_response(
            message=request.message,
            retrieved_chunks=retrieved_chunks,
            chat_history=chat_history,
        ):
            yield token_event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
