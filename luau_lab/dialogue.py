"""Dialogue engine gluing together synthesis, training, and retrieval."""
from __future__ import annotations

import os
import random
from typing import Dict, Iterable, List

import yaml

from .config import LabConfig, export_session_history
from .retrieval import RetrievalClient
from .synthesizer import LuauSynthesizer
from .training import TrainingSuite


class DialogueEngine:
    """A lightweight chatbot orchestrator."""

    def __init__(
        self,
        config: LabConfig,
        synthesizer: LuauSynthesizer,
        retriever: RetrievalClient,
        trainer: TrainingSuite,
        persona_path: str = "persona.yaml",
        heuristics_path: str = "heuristics.yaml",
    ) -> None:
        self.config = config
        self.synthesizer = synthesizer
        self.retriever = retriever
        self.trainer = trainer
        self.history: List[Dict[str, str]] = []
        self.persona = self._load_persona(persona_path)
        self.heuristics_path = heuristics_path
        self._load_heuristics()
        seed = config.style.get("default_random_seed")
        self.synthesizer.update_seed(seed)
        self.random = random.Random(seed)

    # ------------------------------------------------------------------
    def _load_persona(self, path: str) -> Dict[str, Iterable[str]]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
                return data
        return {}

    def _load_heuristics(self) -> None:
        if os.path.exists(self.heuristics_path):
            with open(self.heuristics_path, "r", encoding="utf-8") as handle:
                heuristics = yaml.safe_load(handle) or {}
                self.synthesizer.heuristics.update(heuristics)

    # ------------------------------------------------------------------
    def respond(self, user_input: str) -> str:
        lowered = user_input.lower()
        if any(word in lowered for word in ("hello", "hi", "hey")):
            return self._persona_pick("greeting", default="Hello! Ready to build?")

        if "thank" in lowered:
            return self._persona_pick("thanks", default="You're welcome!")

        if "train" in lowered:
            summary = self.trainer.run_all()
            docs_summary = summary.get("docs", {})
            snippet_count = 0
            for entries in docs_summary.values():
                for entry in entries:
                    if isinstance(entry, dict):
                        snippets = entry.get("snippets")
                        if isinstance(snippets, list):
                            snippet_count += len(snippets)
            prefix = self._persona_pick("training_complete", default="Training complete!")
            return (
                f"{prefix} Loaded {len(summary.get('examples', []))} local examples, "
                f"refreshed naming to {summary.get('heuristics', {}).get('naming', {}).get('function_case', 'camel')}, "
                f"and captured {snippet_count} doc snippets from the allowlist."
            )

        if lowered.startswith("doc ") or lowered.startswith("fetch "):
            parts = user_input.split()
            if len(parts) < 3:
                return "Usage: doc <url> <query>"
            url = parts[1]
            query = " ".join(parts[2:])
            try:
                result = self.retriever.fetch(url, query)
            except ValueError as exc:  # URL blocked
                return str(exc)
            except Exception as exc:  # network issue
                return f"I tried hitting that page but ran into: {exc}"
            if not result.snippets:
                return f"I checked {result.source} but couldn’t spot '{query}' in the text."
            joined = "\n".join(f"- {snippet}" for snippet in result.snippets)
            return f"Here’s what I found on {result.source}:\n{joined}"

        if "explain" in lowered and "```" in user_input:
            code = self._extract_code(user_input)
            explanations = self.synthesizer.explain(code)
            intro = self._persona_pick("explanation_intro", default="Here’s what’s happening:")
            return "\n".join([intro, ""] + explanations)

        if any(keyword in lowered for keyword in ("script", "function", "code")):
            code = self.synthesizer.generate(user_input)
            explanation_lines = self.synthesizer.explain(code)
            intro = self._persona_pick("script_intro", default="Here’s the script I put together:")
            explain_intro = self._persona_pick(
                "explanation_intro", default="Here’s what it does:"
            )
            return "\n".join(
                [
                    intro,
                    "",
                    "```lua",
                    code,
                    "```",
                    "",
                    explain_intro,
                    "",
                    *explanation_lines,
                ]
            )

        return self._persona_pick("fallback", default="Tell me what script you need.")

    # ------------------------------------------------------------------
    def remember(self, user: str, bot: str) -> None:
        self.history.append({"user": user, "bot": bot})
        export_session_history(self.history[-10:])

    def _persona_pick(self, key: str, default: str) -> str:
        options = self.persona.get(key)
        if isinstance(options, list) and options:
            return self.random.choice(options)
        return default

    def _extract_code(self, text: str) -> str:
        start = text.find("```")
        end = text.rfind("```")
        if start == -1 or end == -1 or end <= start:
            return text
        snippet = text[start + 3 : end]
        if snippet.startswith("lua"):
            snippet = snippet[3:]
        return snippet.strip()
