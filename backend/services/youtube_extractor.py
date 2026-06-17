"""Extracts transcripts from YouTube videos given a video URL."""

import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

_PREFERRED_LANGUAGES = ["en", "en-US", "en-GB"]


def _extract_video_id(url: str) -> str:
    """Parse a YouTube video ID out of common URL formats.

    Supports:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - https://www.youtube.com/embed/VIDEO_ID
      - https://www.youtube.com/shorts/VIDEO_ID
    """
    if not url or not isinstance(url, str):
        raise ValueError("YouTube URL must be a non-empty string.")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.lstrip("/")
        if video_id:
            return video_id

    if "youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if video_id:
                return video_id
        for prefix in ("/embed/", "/shorts/", "/v/"):
            if parsed.path.startswith(prefix):
                video_id = parsed.path[len(prefix):].split("/")[0]
                if video_id:
                    return video_id

    # Fallback: an 11-character YouTube ID pattern anywhere in the string.
    match = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})(?:[&?/]|$)", url)
    if match:
        return match.group(1)

    raise ValueError(
        f"Could not parse a video ID from '{url}'. "
        "Expected a youtube.com/watch?v=, youtu.be/, or youtube.com/embed/ URL."
    )


def extract_youtube_transcript(url: str) -> tuple[str, str]:
    """Fetch a transcript for the given YouTube URL.

    Returns (video_id, transcript_text). Tries English first, then falls
    back to whatever transcript language is available. Raises ValueError
    if the URL is invalid or no transcript can be obtained.
    """
    video_id = _extract_video_id(url)

    # youtube-transcript-api v1.x is instance-based (no more static methods).
    api = YouTubeTranscriptApi()

    try:
        transcript_list = api.list(video_id)
    except TranscriptsDisabled as e:
        raise ValueError(
            f"Transcripts are disabled for video '{video_id}'."
        ) from e
    except VideoUnavailable as e:
        raise ValueError(
            f"Video '{video_id}' is unavailable, private, or does not exist."
        ) from e
    except Exception as e:
        raise ValueError(
            f"Could not retrieve transcript info for video '{video_id}': {e}"
        ) from e

    transcript = None
    try:
        transcript = transcript_list.find_transcript(_PREFERRED_LANGUAGES)
    except NoTranscriptFound:
        try:
            transcript = next(iter(transcript_list))
        except StopIteration:
            transcript = None

    if transcript is None:
        raise ValueError(f"No transcript is available for video '{video_id}'.")

    try:
        fetched = transcript.fetch()  # -> FetchedTranscript (iterable of snippets)
    except Exception as e:
        raise ValueError(
            f"Failed to fetch transcript for video '{video_id}': {e}"
        ) from e

    text_parts = [snippet.text.strip() for snippet in fetched]
    transcript_text = " ".join(part for part in text_parts if part)

    if not transcript_text:
        raise ValueError(f"Transcript for video '{video_id}' was empty.")

    return video_id, transcript_text
