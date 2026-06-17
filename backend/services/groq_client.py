"""Streams chat completions from Groq, grounded in retrieved chunk context."""

import asyncio
import json
import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_GROQ_API_KEY = os.getenv("GROQ_API_KEY")
_MODEL = "llama-3.3-70b-versatile"

_client: Groq | None = None
if _GROQ_API_KEY:
    _client = Groq(api_key=_GROQ_API_KEY)


def _build_system_prompt(retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        context_block = "No relevant context was found in any uploaded source."
    else:
        context_parts = []
        for chunk in retrieved_chunks:
            context_parts.append(
                f"[Source: {chunk['source_title']} | Type: {chunk['source_type']}]\n"
                f"{chunk['chunk_text']}"
            )
        context_block = "\n\n---\n\n".join(context_parts)

    return (
        "You are DocuMind AI, a research assistant with access to retrieved "
        "context from the user's uploaded sources — PDFs, web pages, and "
        "YouTube videos. Answer the user's question using ONLY the context "
        "below when it is relevant.\n\n"
        "Whenever you state something that comes from the context, cite the "
        "source it came from using this exact format: [Source: <title>]. "
        "Use the title exactly as given below.\n\n"
        "If the retrieved context does not contain enough information to "
        "answer the question, say so clearly instead of guessing or making "
        "things up.\n\n"
        "=== RETRIEVED CONTEXT ===\n"
        f"{context_block}\n"
        "=== END RETRIEVED CONTEXT ==="
    )


def _run_groq_stream_sync(messages: list[dict]):
    """Blocking call to the Groq SDK — must be run in a thread executor."""
    return _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        stream=True,
    )


async def stream_chat_response(
    message: str,
    retrieved_chunks: list[dict],
    chat_history: list[dict],
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted tokens for a Groq chat completion.

    The Groq SDK call itself is synchronous, so it is executed in a thread
    executor via loop.run_in_executor — calling it directly here would block
    the FastAPI event loop for every other concurrent request.
    """
    if not _client:
        yield f"data: {json.dumps('[Error: GROQ_API_KEY is not set on the server.]')}\n\n"
        yield "data: [DONE]\n\n"
        return

    system_prompt = _build_system_prompt(retrieved_chunks)
    messages = [{"role": "system", "content": system_prompt}]
    for turn in chat_history:
        role = turn.get("role") if isinstance(turn, dict) else getattr(turn, "role", None)
        content = turn.get("content") if isinstance(turn, dict) else getattr(turn, "content", None)
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    loop = asyncio.get_event_loop()

    try:
        stream = await loop.run_in_executor(None, _run_groq_stream_sync, messages)
    except Exception as e:
        yield f"data: {json.dumps(f'[Error contacting Groq API: {e}]')}\n\n"
        yield "data: [DONE]\n\n"
        return

    try:
        # Iterating the Groq stream performs blocking network I/O on each
        # step, so each "next chunk" fetch also runs off the event loop.
        iterator = iter(stream)
        while True:
            try:
                chunk = await loop.run_in_executor(None, next, iterator, None)
            except StopIteration:
                break
            if chunk is None:
                break

            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                # JSON-encode the token so any character it contains
                # (including literal newlines, which a tokenizer can emit
                # as a single "\n\n" token for paragraph breaks) is safely
                # escaped and can never be mistaken for the "\n\n" frame
                # delimiter by the frontend's SSE parser. The frontend
                # JSON.parse()s this payload back into the raw token text.
                yield f"data: {json.dumps(delta)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps(f'[Error during streaming: {e}]')}\n\n"
    finally:
        yield "data: [DONE]\n\n"
