"""Conversation datastore tracking dialogue patterns and outcomes."""
from __future__ import annotations

"""Conversation datastore tracking dialogue patterns and outcomes."""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Iterable, List, Tuple


@dataclass
class ConversationTurn:
    """Snapshot of a single conversational turn."""

    intent: str
    user_affect: str
    tone: str
    structure: str
    lexical_variety: float
    success: float
    reasoning_trace: str


@dataclass
class ConversationPattern:
    """Reusable dialogue strategy with success tracking."""

    pattern_id: str
    intent: str
    tone: str
    structure: str
    register: str
    success_score_by_context: Dict[str, float] = field(default_factory=dict)
    usage_count: int = 0
    overuse_penalty: float = 0.0

    def score(self, context: str) -> float:
        baseline = self.success_score_by_context.get("global", 0.58)
        contextual = self.success_score_by_context.get(context, baseline)
        penalty = min(self.overuse_penalty, 0.4)
        return max(0.0, contextual - penalty)

    def register_success(self, context: str, value: float) -> None:
        current = self.success_score_by_context.get(context, 0.58)
        self.success_score_by_context[context] = current * 0.8 + value * 0.2
        global_score = self.success_score_by_context.get("global", 0.6)
        self.success_score_by_context["global"] = global_score * 0.85 + value * 0.15
        if value > 0.65:
            self.overuse_penalty = max(0.0, self.overuse_penalty - 0.05)
        else:
            self.overuse_penalty = min(0.4, self.overuse_penalty + 0.03)


_DEFAULT_PATTERNS: Tuple[ConversationPattern, ...] = (
    ConversationPattern(
        pattern_id="teach.example.recap",
        intent="explain",
        tone="warm",
        structure="teach→example→recap",
        register="technical_conversational",
        success_score_by_context={"global": 0.64},
    ),
    ConversationPattern(
        pattern_id="coach.plan.challenge",
        intent="problem_solving",
        tone="steady",
        structure="diagnose→strategy→next-step",
        register="analytical",
        success_score_by_context={"global": 0.63},
    ),
    ConversationPattern(
        pattern_id="clarify.then.answer",
        intent="question",
        tone="curious",
        structure="clarify→answer→invite",
        register="technical_conversational",
        success_score_by_context={"global": 0.61},
    ),
    ConversationPattern(
        pattern_id="story.then.lesson",
        intent="motivate",
        tone="encouraging",
        structure="story→insight→encourage",
        register="narrative",
        success_score_by_context={"global": 0.62},
    ),
    ConversationPattern(
        pattern_id="universal.balance",
        intent="universal",
        tone="balanced",
        structure="acknowledge→analysis→summary",
        register="balanced",
        success_score_by_context={"global": 0.6},
    ),
    ConversationPattern(
        pattern_id="dialogue.loop.reflect",
        intent="conversation",
        tone="warm",
        structure="greet→explore→respond→reflect",
        register="dialogue_support",
        success_score_by_context={"global": 0.62},
    ),
    ConversationPattern(
        pattern_id="code.review.sequence",
        intent="problem_solving",
        tone="steady",
        structure="diagnose→code→next-step",
        register="engineering",
        success_score_by_context={"global": 0.64},
    ),
)


class ConversationDatastore:
    """Tracks dialogue patterns, outcomes, and assists in style selection."""

    def __init__(self) -> None:
        self._turn_log: Deque[ConversationTurn] = deque(maxlen=250)
        self._patterns: Dict[str, ConversationPattern] = {
            pattern.pattern_id: pattern for pattern in _DEFAULT_PATTERNS
        }
        self._recent_patterns: Deque[str] = deque(maxlen=12)

    # Public API -----------------------------------------------------------
    def select_pattern(self, intent: str, user_affect: str) -> ConversationPattern:
        """Return the best-scoring pattern for the given conversational context."""

        normalized_intent = intent or "universal"
        context = f"{normalized_intent}|{user_affect or 'neutral'}"
        candidates = [
            pattern
            for pattern in self._patterns.values()
            if pattern.intent in {normalized_intent, "universal"}
        ]
        if not candidates:
            candidates = list(self._patterns.values())
        best_pattern = max(
            candidates,
            key=lambda pattern: self._score_with_novelty(pattern, context),
        )
        self._register_usage(best_pattern.pattern_id)
        return best_pattern

    def register_turn(
        self,
        pattern_id: str,
        intent: str,
        user_affect: str,
        tone: str,
        structure: str,
        lexical_variety: float,
        success: float,
        reasoning_trace: str,
    ) -> None:
        """Persist conversational telemetry for future selection."""

        turn = ConversationTurn(
            intent=intent,
            user_affect=user_affect,
            tone=tone,
            structure=structure,
            lexical_variety=lexical_variety,
            success=success,
            reasoning_trace=reasoning_trace,
        )
        self._turn_log.append(turn)
        context = f"{intent}|{user_affect or 'neutral'}"
        pattern = self._patterns.get(pattern_id)
        if pattern:
            pattern.usage_count += 1
            adjusted_success = 0.5 * success + 0.5 * min(1.0, lexical_variety)
            pattern.register_success(context, adjusted_success)

    def ingest_highlights(
        self, highlights: Iterable[Tuple[str, str, str]]
    ) -> None:
        """Promote new dialogue strategies extracted from autonomous training."""

        for topic, summary, insight in highlights:
            lowered_topic = topic.lower()
            lowered_summary = summary.lower()
            if not any(
                keyword in lowered_topic or keyword in lowered_summary
                for keyword in ("conversation", "communication", "story", "tone")
            ):
                continue
            pattern_id = f"auto::{topic.replace('::', '_')}"
            if pattern_id in self._patterns:
                continue
            structure = self._infer_structure_from_summary(lowered_summary)
            tone = "encouraging" if "story" in lowered_summary else "balanced"
            intent = "question" if "ask" in lowered_summary else "explain"
            register = "narrative" if "story" in lowered_summary else "analytical"
            pattern = ConversationPattern(
                pattern_id=pattern_id,
                intent=intent,
                tone=tone,
                structure=structure,
                register=register,
                success_score_by_context={"global": 0.6},
            )
            self._patterns[pattern_id] = pattern

    def all_patterns(self) -> List[ConversationPattern]:
        return list(self._patterns.values())

    # Internal helpers ----------------------------------------------------
    def _score_with_novelty(self, pattern: ConversationPattern, context: str) -> float:
        novelty_bonus = 0.04
        if pattern.pattern_id in self._recent_patterns:
            index = list(self._recent_patterns).index(pattern.pattern_id)
            novelty_bonus = max(0.0, novelty_bonus - 0.01 * (index + 1))
        else:
            novelty_bonus = 0.05
        return pattern.score(context) + novelty_bonus

    def _register_usage(self, pattern_id: str) -> None:
        self._recent_patterns.append(pattern_id)
        for existing in self._patterns.values():
            if existing.pattern_id == pattern_id:
                existing.overuse_penalty = min(0.4, existing.overuse_penalty + 0.015)
            else:
                existing.overuse_penalty = max(0.0, existing.overuse_penalty - 0.01)

    def _infer_structure_from_summary(self, summary: str) -> str:
        if "debate" in summary or "argument" in summary:
            return "acknowledge→contrast→resolve"
        if "story" in summary or "narrative" in summary:
            return "story→lesson→next-step"
        if "question" in summary or "ask" in summary:
            return "clarify→answer→invite"
        if "practice" in summary or "guide" in summary:
            return "teach→drill→recap"
        return "acknowledge→analysis→summary"
