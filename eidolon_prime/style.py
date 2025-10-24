"""Style profile selection for discourse moves."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from .retrieval import RetrievedEvidence
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .planner import PlanOutline


@dataclass
class StyleProfileSpec:
    name: str
    hedges: Dict[float, str]
    openers: List[str]
    connectors: List[str]
    banlist: List[str]
    cadence: Dict[str, float]


@dataclass
class StyleSelection:
    profile: StyleProfileSpec
    tone: str

    def opening(self, operator: str) -> str:
        base = self.profile.openers[0 if operator.lower() == "explain" else -1]
        return f"{base}"

    def action_prompt(self, focus: str) -> str:
        return f"Consider prototyping {focus} before widening scope."

    def closing(self, goal: str, evidence: Sequence[RetrievedEvidence]) -> str:
        if not evidence:
            return "I recommend revisiting this after gathering fresh references."
        hedge = self._hedge(self.profile.hedges)
        return f"{hedge.capitalize()}, this plan keeps {goal.lower()} aligned with the strongest sources I verified."

    def _hedge(self, hedges: Dict[float, str]) -> str:
        threshold = sorted(hedges.items(), key=lambda item: item[0])[-1]
        return threshold[1]

    def to_dict(self) -> Dict[str, object]:
        return {"profile": self.profile.name, "tone": self.tone}


class StyleProfile:
    """Registry of style profiles and selection logic."""

    def __init__(self) -> None:
        self._profiles = self._default_profiles()

    def select_profile(self, plan: "PlanOutline", focus_terms: Sequence[str]) -> StyleSelection:
        if any("code" in term.lower() or "lua" in term.lower() for term in focus_terms):
            spec = self._profiles["mentor_playful"]
            tone = "technical"
        elif any("risk" in step.focus.lower() for step in plan.steps):
            spec = self._profiles["cautious"]
            tone = "cautious"
        else:
            spec = self._profiles["mentor_playful"]
            tone = "confident"
        return StyleSelection(profile=spec, tone=tone)

    def _default_profiles(self) -> Dict[str, StyleProfileSpec]:
        return {
            "mentor_playful": StyleProfileSpec(
                name="mentor_playful",
                hedges={0.5: "might", 0.7: "likely", 0.9: "confidently"},
                openers=["Here's the gist:", "Short version:"],
                connectors=["So", "Meanwhile", "By contrast"],
                banlist=["in order to", "very unique"],
                cadence={"mean": 20, "stdev": 8},
            ),
            "cautious": StyleProfileSpec(
                name="cautious",
                hedges={0.4: "could", 0.6: "probably", 0.85: "strongly"},
                openers=["Let's outline:", "Key takeaways:"],
                connectors=["Next", "However", "Additionally"],
                banlist=["obviously", "of course"],
                cadence={"mean": 18, "stdev": 6},
            ),
        }
