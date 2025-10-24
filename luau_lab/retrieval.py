"""Retrieve curated knowledge from allowed sources."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

import requests
from bs4 import BeautifulSoup


@dataclass
class RetrievalResult:
    source: str
    snippets: List[str]


class RetrievalClient:
    """A whitelisted HTTP retriever."""

    def __init__(self, allowed_sources: Iterable[str]) -> None:
        self.allowed_sources = list(allowed_sources)

    def is_allowed(self, url: str) -> bool:
        return any(url.startswith(prefix) for prefix in self.allowed_sources)

    def fetch(self, url: str, query: str) -> RetrievalResult:
        if not self.is_allowed(url):
            raise ValueError(f"URL not allowed: {url}")

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        lines = [line.strip() for line in soup.get_text().splitlines() if line.strip()]
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        snippets = [line for line in lines if pattern.search(line)]

        return RetrievalResult(source=url, snippets=snippets[:8])
