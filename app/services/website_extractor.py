"""
Website content extractor.
Fetches the page, strips HTML, and returns cleaned text + metadata.
"""

import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.utils.validators import validate_url


class WebsiteExtractor:
    """Fetches a URL and extracts cleaned text content and metadata."""

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async def extract(self, url: str) -> dict:
        """
        Fetch the URL and return a dict with:
          - url, title, meta_description, meta_keywords,
          - headings, body_text, links, structured_content
        """
        async with httpx.AsyncClient(
            follow_redirects=False,
            trust_env=False,
            timeout=settings.request_timeout,
            headers=self._HEADERS,
        ) as client:
            try:
                current_url = url
                for redirect_count in range(6):
                    is_valid, error = validate_url(current_url)
                    if not is_valid:
                        raise ValueError(error)
                    async with client.stream("GET", current_url) as response:
                        if response.status_code in (301, 302, 303, 307, 308):
                            location = response.headers.get("location")
                            if not location or redirect_count == 5:
                                raise ValueError("Too many or invalid website redirects.")
                            current_url = urljoin(current_url, location)
                            continue

                        response.raise_for_status()
                        content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                        if content_type not in ("text/html", "application/xhtml+xml"):
                            raise ValueError("The URL did not return an HTML website.")

                        max_response_bytes = settings.max_content_length * 20
                        content_length = response.headers.get("content-length")
                        if content_length:
                            try:
                                declared_length = int(content_length)
                            except ValueError as exc:
                                raise ValueError("Website returned an invalid Content-Length header.") from exc
                            if declared_length < 0:
                                raise ValueError("Website returned an invalid Content-Length header.")
                            if declared_length > max_response_bytes:
                                raise ValueError("Website response is too large to analyze.")

                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > max_response_bytes:
                                raise ValueError("Website response is too large to analyze.")
                        try:
                            encoding = response.encoding or "utf-8"
                        except LookupError:
                            encoding = "utf-8"
                        html = bytes(body).decode(encoding, errors="replace")
                        final_url = str(response.url)
                        break
                else:
                    raise ValueError("Too many website redirects.")
            except httpx.TimeoutException:
                raise ValueError(f"Request timed out while fetching: {url}")
            except httpx.HTTPStatusError as exc:
                raise ValueError(
                    f"HTTP {exc.response.status_code} error fetching {url}"
                )
            except httpx.RequestError as exc:
                raise ValueError(f"Network error fetching {url}: {exc}")

        return self._parse_html(final_url, html)

    def _parse_html(self, url: str, html: str) -> dict:
        soup = BeautifulSoup(html, "lxml")

        # Remove noise tags
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        # --- Basic metadata ---
        title = self._get_title(soup)
        meta_desc = self._get_meta(soup, "description")
        meta_keywords = self._get_meta(soup, "keywords")
        og_description = self._get_og(soup, "description")
        og_site_name = self._get_og(soup, "site_name")

        # --- Headings ---
        headings = {
            "h1": [h.get_text(strip=True) for h in soup.find_all("h1")][:5],
            "h2": [h.get_text(strip=True) for h in soup.find_all("h2")][:10],
            "h3": [h.get_text(strip=True) for h in soup.find_all("h3")][:10],
        }

        # --- Body text (truncated) ---
        body_text = soup.get_text(separator=" ", strip=True)
        body_text = re.sub(r"\s+", " ", body_text)
        body_text = body_text[: settings.max_content_length]

        # --- Internal / external links ---
        base_domain = (urlparse(url).hostname or "").lower()
        links = []
        for a in soup.find_all("a", href=True)[:50]:
            href = a["href"]
            full_url = urljoin(url, href)
            link_text = a.get_text(strip=True)
            if link_text and len(link_text) > 2:
                links.append(
                    {
                        "text": link_text[:80],
                        "href": full_url,
                        "is_internal": (urlparse(full_url).hostname or "").lower() == base_domain,
                    }
                )

        # --- Structured page sections ---
        structured = self._extract_sections(soup)

        return {
            "url": url,
            "domain": base_domain,
            "title": title,
            "meta_description": meta_desc or og_description or "",
            "meta_keywords": meta_keywords or "",
            "site_name": og_site_name or base_domain,
            "headings": headings,
            "body_text": body_text,
            "links": links[:30],
            "structured_content": structured,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _get_title(soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else ""

    @staticmethod
    def _get_meta(soup: BeautifulSoup, name: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    @staticmethod
    def _get_og(soup: BeautifulSoup, prop: str) -> Optional[str]:
        tag = soup.find("meta", property=f"og:{prop}")
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    @staticmethod
    def _extract_sections(soup: BeautifulSoup) -> list[dict]:
        """Group content by h2 sections."""
        sections = []
        for h2 in soup.find_all("h2")[:8]:
            content_parts = []
            for sibling in h2.find_next_siblings():
                if sibling.name == "h2":
                    break
                text = sibling.get_text(strip=True)
                if text:
                    content_parts.append(text)
            if content_parts:
                sections.append(
                    {
                        "heading": h2.get_text(strip=True),
                        "content": " ".join(content_parts)[:500],
                    }
                )
        return sections
