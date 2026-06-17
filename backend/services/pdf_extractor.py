"""Extracts text content from PDF files."""

import io
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError


def extract_pdf_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from a PDF given as raw bytes.

    Raises ValueError with a clear, user-facing message if the PDF is
    empty, encrypted without a usable password, corrupted, or contains
    no extractable text.
    """
    if not file_bytes:
        raise ValueError(f"'{filename}' is empty — no content to read.")

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except PdfReadError as e:
        raise ValueError(f"'{filename}' could not be read as a PDF: {e}") from e
    except Exception as e:
        raise ValueError(f"'{filename}' could not be opened: {e}") from e

    if reader.is_encrypted:
        try:
            # Many "encrypted" PDFs only restrict permissions and open with
            # an empty password. If this fails, surface a clear error.
            reader.decrypt("")
        except Exception as e:
            raise ValueError(
                f"'{filename}' is password-protected and cannot be read."
            ) from e

    if len(reader.pages) == 0:
        raise ValueError(f"'{filename}' has no pages.")

    page_texts = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            # Skip pages that fail to extract rather than failing the whole document.
            page_text = ""
        page_texts.append(page_text)

    full_text = "\n".join(page_texts)
    full_text = re.sub(r"[ \t]+", " ", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    full_text = full_text.strip()

    if not full_text:
        raise ValueError(
            f"'{filename}' contains no extractable text "
            "(it may be a scanned image with no OCR text layer)."
        )

    return full_text
