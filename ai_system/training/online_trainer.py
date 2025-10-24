"""Online training utilities for expanding the knowledge base safely."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable

import requests
from bs4 import BeautifulSoup

from ai_system.config import SystemConfig, TrustedSource
from ai_system.core.memory import KnowledgeBase


def _extract_text(html: str, selectors: Iterable[str] | None = None) -> str:
    """Collapse HTML into readable text constrained by CSS selectors."""

    soup = BeautifulSoup(html, "html.parser")
    if selectors:
        chunks = []
        for selector in selectors:
            for element in soup.select(selector):
                chunks.append(element.get_text(" ", strip=True))
        if chunks:
            return "\n\n".join(chunks)
    return soup.get_text(" ", strip=True)


class OnlineTrainer:
    """Harvests new material from trusted sources and stores it in the KB."""

    def __init__(self, config: SystemConfig, state_dir: Path | None = None) -> None:
        self.config = config
        self.knowledge = KnowledgeBase(config.data_root / "knowledge")
        self.state_path = (state_dir or config.data_root) / "online_state.json"
        self.state: Dict[str, str] = {}
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text())

    def _should_crawl(self, source: TrustedSource) -> bool:
        key = source.name
        if key not in self.state:
            return True
        last_run = datetime.fromisoformat(self.state[key])
        return datetime.utcnow() - last_run >= timedelta(hours=source.crawl_frequency_hours)

    def _fetch(self, source: TrustedSource) -> str:
        response = requests.get(source.url, timeout=30)
        response.raise_for_status()
        return _extract_text(response.text, selectors=["article", "main", "body"])

    def _record_run(self, source: TrustedSource) -> None:
        self.state[source.name] = datetime.utcnow().isoformat()
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def harvest(self) -> Dict[str, str]:
        """Fetch and persist new documents, returning stored paths."""

        stored: Dict[str, str] = {}
        for source in self.config.trusted_sources:
            if not self._should_crawl(source):
                continue
            try:
                text = self._fetch(source)
            except Exception as exc:  # noqa: BLE001 - network resilience priority
                stored[source.name] = f"error: {exc}"
                continue
            identifier = f"online_{source.name}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            stored_path = self.knowledge.store(identifier, text)
            stored[source.name] = str(stored_path)
            self._record_run(source)
        return stored

