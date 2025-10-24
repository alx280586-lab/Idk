"""Seed training corpus for Eidolon Prime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .memory import MemoryWeb


@dataclass(frozen=True)
class SeedLesson:
    """Structured representation of a curated training lesson."""

    topic: str
    content: str
    confidence: float


DOMAINS: List[str] = [
    "systems thinking",
    "incident management",
    "observability",
    "software architecture",
    "continuous delivery",
    "testing strategy",
    "developer experience",
    "security engineering",
    "data governance",
    "applied ethics",
    "performance tuning",
    "infrastructure as code",
    "resilience engineering",
    "product discovery",
    "risk management",
    "knowledge management",
    "documentation systems",
    "feedback design",
    "workflow automation",
    "collaboration rituals",
    "design systems",
    "usability research",
    "machine learning ops",
    "privacy engineering",
    "compliance automation",
]

ASPECTS: List[str] = [
    "clarity",
    "alignment",
    "experimentation",
    "measurement",
    "feedback",
    "governance",
    "automation",
    "verification",
    "mentorship",
    "scalability",
]

SCENARIOS: List[str] = [
    "during onboarding initiatives",
    "while scaling across teams",
    "when recovering from incidents",
    "while exploring emerging requirements",
]

BENEFITS: List[str] = [
    "reduces cognitive load for contributors",
    "creates a reliable trail of evidence",
    "keeps knowledge adaptive as the system evolves",
    "shortens the feedback loop for stakeholders",
    "balances risk with innovation",
    "encourages accountable collaboration",
    "strengthens organizational memory",
    "turns implicit heuristics into explicit playbooks",
    "spotlights bottlenecks before they escalate",
    "aligns day-to-day work with long-term vision",
]


def _generate_seed_lessons() -> Iterable[SeedLesson]:
    """Deterministically expand small concept sets into a rich corpus."""

    for domain_index, domain in enumerate(DOMAINS):
        for aspect_index, aspect in enumerate(ASPECTS):
            for scenario_index, scenario in enumerate(SCENARIOS):
                benefit_index = (domain_index + aspect_index + scenario_index) % len(BENEFITS)
                benefit = BENEFITS[benefit_index]
                topic = f"{domain}::{aspect}"
                content = (
                    f"Within {domain}, practitioners cultivate {aspect} {scenario} "
                    f"so that the initiative {benefit}."
                )
                yield SeedLesson(topic=topic, content=content, confidence=0.85)


def load_seed_training_corpus(memory: MemoryWeb) -> int:
    """Populate the memory web with a thousand curated lessons if absent."""

    if memory.count_by_provenance("seed_corpus") > 0:
        return 0
    count = 0
    for lesson in _generate_seed_lessons():
        memory.record(lesson.topic, lesson.content, lesson.confidence, "seed_corpus")
        count += 1
    return count
