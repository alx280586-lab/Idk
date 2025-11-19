"""Build relationships from wikilinks and categories."""
from __future__ import annotations

from typing import List, Dict


def parse_links(text: str) -> List[Dict[str, str]]:
    links = []
    start = 0
    while True:
        start = text.find("[[", start)
        if start == -1:
            break
        end = text.find("]]", start)
        if end == -1:
            break
        title = text[start + 2 : end]
        links.append({"target": title, "type": "mentions"})
        start = end + 2
    return links


def parse_categories(text: str) -> List[str]:
    return [line.split(":", 1)[-1].strip() for line in text.splitlines() if "Category:" in line]


__all__ = ["parse_links", "parse_categories"]
