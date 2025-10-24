"""Message comprehension utilities for semantic analysis."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "to",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "you",
    "your",
}

_POSITIVE_MARKERS = {"awesome", "excited", "fantastic", "glad", "good", "great", "love", "thanks", "thank"}
_NEGATIVE_MARKERS = {"angry", "bad", "confused", "frustrated", "sad", "stressed", "upset", "worried"}
_URGENCY_MARKERS = {"asap", "urgent", "critical", "now", "immediately"}
_COMMAND_MARKERS = {"build", "design", "explain", "fix", "guide", "help", "implement", "plan", "solve"}


@dataclass
class MessageUnderstanding:
    """Structured interpretation of a user message."""

    original: str
    sentences: List[str]
    tokens: List[str]
    keywords: List[str]
    focus_terms: List[str]
    focus_pairs: List[str]
    question: bool
    affect: str
    urgency: bool
    command_clauses: List[str]

    def focus_text(self) -> str:
        """Return a condensed representation of the user's focus."""

        if self.focus_pairs:
            return " ; ".join(self.focus_pairs[:4])
        return " ".join(self.focus_terms[:6])

    def topic_hint(self) -> str:
        if self.focus_pairs:
            return " / ".join(self.focus_pairs[:3])
        if self.focus_terms:
            return " / ".join(self.focus_terms[:3])
        if self.sentences:
            return self.sentences[0][:48]
        return self.original[:48]

    def summary(self) -> str:
        sentence_part = f"sentences={len(self.sentences)}"
        focus_part = f"focus_terms={', '.join(self.focus_terms[:6]) or 'n/a'}"
        pair_part = f"focus_pairs={', '.join(self.focus_pairs[:4]) or 'n/a'}"
        affect_part = f"affect={self.affect or 'neutral'}"
        urgency_part = "urgent" if self.urgency else "steady"
        commands = ", ".join(self.command_clauses) or "none"
        return (
            f"Comprehension summary → {sentence_part}; {focus_part}; {pair_part};"
            f" {affect_part}; urgency={urgency_part}; commands={commands}"
        )

    def highlights(self) -> List[str]:
        """Return human-friendly snippets describing what was understood."""

        snippets: List[str] = []
        if self.focus_terms:
            primary_terms = ", ".join(self.focus_terms[:4])
            snippets.append(f"You centred the conversation on {primary_terms}.")
        if self.focus_pairs:
            phrase_text = "; ".join(self.focus_pairs[:3])
            snippets.append(f"Your sentences connect ideas like {phrase_text}.")
        if self.command_clauses:
            command = self.command_clauses[0]
            snippets.append(f"You explicitly asked me to {command}.")
        if not snippets:
            snippets.append("I'm digesting every word so I mirror your intent accurately.")
        return snippets


class MessageComprehender:
    """Lightweight semantic analyser that inspects every word in a message."""

    _token_pattern = re.compile(r"[A-Za-z0-9']+")

    def analyse(self, text: str) -> MessageUnderstanding:
        stripped = text.strip()
        sentences = [segment.strip() for segment in re.split(r"[.!?]+", stripped) if segment.strip()]
        tokens = [token.lower() for token in self._token_pattern.findall(stripped)]
        keywords = [token for token in tokens if token not in _STOPWORDS]
        focus_terms = self._compute_focus_terms(keywords)
        focus_pairs = self._compute_focus_pairs(keywords)
        question = "?" in stripped or any(
            token in {"how", "what", "why", "where", "when", "who"} for token in tokens[:3]
        )
        affect = self._detect_affect(tokens)
        urgency = any(marker in tokens for marker in _URGENCY_MARKERS)
        command_clauses = self._extract_command_clauses(tokens, sentences)
        return MessageUnderstanding(
            original=text,
            sentences=sentences,
            tokens=tokens,
            keywords=keywords,
            focus_terms=focus_terms,
            focus_pairs=focus_pairs,
            question=question,
            affect=affect,
            urgency=urgency,
            command_clauses=command_clauses,
        )

    def _compute_focus_terms(self, keywords: Iterable[str]) -> List[str]:
        counts = Counter(keywords)
        ordered = [term for term, _ in counts.most_common() if len(term) > 2]
        return ordered[:12]

    def _compute_focus_pairs(self, keywords: List[str]) -> List[str]:
        pairs: List[str] = []
        for first, second in zip(keywords, keywords[1:]):
            if first in _STOPWORDS or second in _STOPWORDS:
                continue
            if len(first) <= 2 or len(second) <= 2:
                continue
            pair = f"{first} {second}"
            pairs.append(pair)
        seen: Dict[str, None] = {}
        ordered_pairs = []
        for pair in pairs:
            if pair not in seen:
                seen[pair] = None
                ordered_pairs.append(pair)
        return ordered_pairs[:12]

    def _detect_affect(self, tokens: Iterable[str]) -> str:
        tokens_set = set(tokens)
        if tokens_set & _NEGATIVE_MARKERS:
            return "stressed"
        if tokens_set & _POSITIVE_MARKERS:
            return "positive"
        return "neutral"

    def _extract_command_clauses(self, tokens: List[str], sentences: List[str]) -> List[str]:
        clauses: List[str] = []
        lower_sentences = [sentence.lower() for sentence in sentences]
        for marker in _COMMAND_MARKERS:
            for sentence in lower_sentences:
                if marker in sentence:
                    clauses.append(sentence.strip())
                    break
        if not clauses and any(token in _COMMAND_MARKERS for token in tokens):
            clauses.append(" ".join(tokens))
        return clauses

__all__ = ["MessageComprehender", "MessageUnderstanding"]
