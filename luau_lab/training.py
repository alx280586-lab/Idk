"""Single entry-point training suite for the Luau Synthesis Lab."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml

from .config import LabConfig
from .retrieval import RetrievalClient


@dataclass
class TrainingResult:
    naming: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, object] = field(default_factory=dict)
    examples_used: List[str] = field(default_factory=list)


class TrainingSuite:
    """Orchestrates all training passes from one script."""

    def __init__(
        self,
        config: LabConfig,
        heuristics_path: str = "heuristics.yaml",
        retriever: Optional[RetrievalClient] = None,
    ) -> None:
        self.config = config
        self.heuristics_path = heuristics_path
        self.retriever = retriever
        self.heuristics: Dict[str, Dict[str, object]] = {}
        if os.path.exists(heuristics_path):
            with open(heuristics_path, "r", encoding="utf-8") as handle:
                self.heuristics = yaml.safe_load(handle) or {}
        docs_cache_dir = self.config.training.get("docs_cache_dir", "data/docs_cache")
        self.docs_cache_dir = Path(docs_cache_dir)
        if self.retriever:
            self.docs_cache_dir.mkdir(parents=True, exist_ok=True)

    # Section 1: Example mining -----------------------------------------
    def train_from_examples(self) -> TrainingResult:
        examples_dir = Path(self.config.training.get("examples_dir", "data/examples"))
        scripts = list(examples_dir.glob("*.lua")) + list(examples_dir.glob("*.luau"))
        naming_counts = {"camel": 0, "pascal": 0, "snake": 0}
        preferences: Dict[str, object] = {}

        for script in scripts:
            text = script.read_text(encoding="utf-8")
            self._harvest_naming(text, naming_counts)
            if "Random.new" in text:
                preferences["prefer_random_new"] = True
            if "CollectionService" in text:
                preferences.setdefault("collection_service_tags", True)

        naming_choice = max(naming_counts, key=naming_counts.get) if scripts else "camel"
        return TrainingResult(
            naming={"function_case": naming_choice, "variable_case": naming_choice},
            preferences=preferences,
            examples_used=[str(script) for script in scripts],
        )

    # Section 2: Test metadata -----------------------------------------
    def train_from_tests(self) -> Dict[str, object]:
        tests_dir = Path(self.config.training.get("tests_dir", "data/tests"))
        expectations: Dict[str, object] = {}
        for test_file in tests_dir.glob("*.json"):
            payload = json.loads(test_file.read_text(encoding="utf-8"))
            expected = payload.get("expected")
            if expected:
                expectations[payload.get("name", test_file.stem)] = expected
        return expectations

    # Section 3: Persona shaping ---------------------------------------
    def load_persona(self) -> Dict[str, Iterable[str]]:
        persona_path = Path(self.config.training.get("persona_file", "persona.yaml"))
        if not persona_path.exists():
            return {}
        with open(persona_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    # Section 4: Documentation harvesting -------------------------------
    def train_from_docs(self) -> Dict[str, List[Dict[str, object]]]:
        if not self.retriever:
            return {}

        queries: List[str] = (
            self.config.training.get("doc_queries")
            or self.config.docs.get("queries")
            or ["spawn", "RemoteEvent", "PathfindingService"]
        )

        summary: Dict[str, List[Dict[str, object]]] = {}
        for source in self.config.allowed_sources:
            source_entries: List[Dict[str, object]] = []
            for query in queries:
                try:
                    result = self.retriever.fetch(source, query)
                except Exception as exc:  # Network or parsing issues
                    source_entries.append({"query": query, "error": str(exc)})
                    continue

                snippets = result.snippets
                source_entries.append({"query": query, "snippets": snippets})
                self._persist_doc_snippets(source, query, snippets)

            summary[source] = source_entries
        return summary

    # Section 5: Persist heuristics ------------------------------------
    def save(self, result: TrainingResult) -> None:
        self.heuristics.setdefault("naming", {}).update(result.naming)
        self.heuristics.setdefault("preferences", {}).update(result.preferences)
        with open(self.heuristics_path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(self.heuristics, handle, sort_keys=False)

    # Section 6: Public API --------------------------------------------
    def run_all(self) -> Dict[str, object]:
        result = self.train_from_examples()
        expectations = self.train_from_tests()
        self.save(result)
        persona = self.load_persona()
        docs = self.train_from_docs()
        return {
            "heuristics": self.heuristics,
            "examples": result.examples_used,
            "expectations": expectations,
            "persona": persona,
            "docs": docs,
        }

    # Helpers -----------------------------------------------------------
    def _harvest_naming(self, text: str, counts: Dict[str, int]) -> None:
        pattern = re.compile(r"function\s+([a-zA-Z0-9_]+)")
        for match in pattern.finditer(text):
            name = match.group(1)
            if "_" in name:
                counts["snake"] += 1
            elif name and name[0].isupper():
                counts["pascal"] += 1
            else:
                counts["camel"] += 1

    def _persist_doc_snippets(self, source: str, query: str, snippets: List[str]) -> None:
        if not snippets:
            return
        safe_source = re.sub(r"[^a-zA-Z0-9]+", "_", source).strip("_") or "source"
        safe_query = re.sub(r"[^a-zA-Z0-9]+", "_", query).strip("_") or "query"
        path = self.docs_cache_dir / f"{safe_source}_{safe_query}.json"
        payload = {"source": source, "query": query, "snippets": snippets}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)


if __name__ == "__main__":
    config = LabConfig.from_dict({})
    trainer = TrainingSuite(config)
    summary = trainer.run_all()
    print(json.dumps(summary, indent=2))
