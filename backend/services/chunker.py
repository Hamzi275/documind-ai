"""Splits raw text into overlapping chunks suitable for embedding."""

import re


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks of roughly `chunk_size` characters.

    Tries to break near a sentence boundary (. ! ?) close to the chunk_size
    limit instead of cutting mid-word. Handles very short texts (returned as
    a single chunk) and very long texts (thousands of chunks) without
    crashing or looping forever.
    """
    if not text:
        return []

    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if overlap < 0 or overlap >= chunk_size:
        # Guard against an overlap that would cause the window to never advance.
        overlap = min(max(overlap, 0), chunk_size // 2)

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    text_len = len(text)
    sentence_end_chars = (".", "!", "?")
    # Look for a sentence boundary within this trailing window of the chunk.
    boundary_search_window = max(int(chunk_size * 0.2), 30)

    while start < text_len:
        hard_end = min(start + chunk_size, text_len)

        if hard_end >= text_len:
            end = text_len
        else:
            end = hard_end
            search_floor = max(start, hard_end - boundary_search_window)
            best_boundary = -1
            for i in range(hard_end, search_floor, -1):
                if text[i - 1] in sentence_end_chars:
                    best_boundary = i
                    break
            if best_boundary != -1:
                end = best_boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break

        next_start = end - overlap
        # Always make forward progress, even if overlap is large relative to
        # the chunk just produced.
        if next_start <= start:
            next_start = start + 1
        start = next_start

    return chunks
