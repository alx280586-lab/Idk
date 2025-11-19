"""Stream Wikipedia articles from XML dumps."""
from __future__ import annotations

from typing import Iterator, Tuple


def stream_articles(dump_path: str) -> Iterator[Tuple[str, str, str]]:
    """Yield (title, text, page_id) from a simplified dump reader."""
    import bz2
    import re

    with bz2.open(dump_path, "rt", encoding="utf-8", errors="ignore") as f:
        buffer = []
        title = page_id = None
        for line in f:
            if "<title>" in line:
                title = re.sub(r"<[^>]+>", "", line).strip()
            elif "<id>" in line and page_id is None:
                page_id = re.sub(r"<[^>]+>", "", line).strip()
            elif "<text" in line:
                buffer = []
            elif "</text>" in line:
                yield title or "", "".join(buffer), page_id or ""
                buffer = []
                title = page_id = None
            else:
                buffer.append(line)
