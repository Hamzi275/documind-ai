"""Scrapes a web page and returns its title and visible text content."""

import re

import requests
from bs4 import BeautifulSoup

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_REMOVE_TAGS = ("script", "style", "nav", "footer", "header", "noscript")


def scrape_url(url: str) -> tuple[str, str]:
    """Fetch `url` and return (title, text).

    Raises ValueError on an invalid URL, request timeout, non-200 status,
    or empty extracted content.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")

    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(
            f"'{url}' is not a valid URL — it must start with http:// or https://"
        )

    try:
        response = requests.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=10,
        )
    except requests.exceptions.Timeout as e:
        raise ValueError(f"Request to '{url}' timed out after 10 seconds.") from e
    except requests.exceptions.ConnectionError as e:
        raise ValueError(f"Could not connect to '{url}': {e}") from e
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch '{url}': {e}") from e

    if response.status_code != 200:
        raise ValueError(
            f"'{url}' returned HTTP status {response.status_code}, expected 200."
        )

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text().strip() if title_tag and title_tag.get_text().strip() else url

    for tag_name in _REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    raw_text = soup.get_text(separator="\n")
    text = re.sub(r"[ \t]+", " ", raw_text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    text = text.strip()

    if not text:
        raise ValueError(f"No readable text content was found at '{url}'.")

    return title, text
