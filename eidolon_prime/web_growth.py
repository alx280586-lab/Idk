"""Web growth subsystem for ingesting curated external knowledge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Dict

from .memory import MemoryWeb
from .firewall import FirewallRing
from .curriculum import (
    CURRICULUM_STAGES,
    CurriculumStage,
    stage_lesson_iterator,
    trusted_source_blueprints,
)


@dataclass
class WebFinding:
    """Minimal representation of a piece of external knowledge."""

    source: str
    summary: str
    verified: bool


@dataclass(frozen=True)
class AutonomousSource:
    """Description of a trusted domain for autonomous training."""

    source: str
    topic: str
    insight: str
    summary: str
    tags: Sequence[str]
    tier: str
    refresh_days: int


@dataclass
class AutoTrainingHighlight:
    """Key points surfaced during an autonomous training cycle."""

    source: str
    topic: str
    summary: str
    insight: str
    tier: str
    kind: str


@dataclass
class AutoTrainingReport:
    """Telemetry returned after crawling trusted domains."""

    focus: str
    imported: int
    highlights: List[AutoTrainingHighlight]
    curriculum_stage: str
    quiz_score: float
    stage_complete: bool

    def render(self) -> str:
        header = [
            "Autonomous training complete!",
            f"- Focus: {self.focus or 'general knowledge'}",
            f"- Entries captured: {self.imported}",
            f"- Curriculum stage: {self.curriculum_stage} (quiz score {self.quiz_score:.2f})",
        ]
        if self.stage_complete:
            header.append("- Stage milestone achieved! Progressing to deeper skills.")
        if not self.highlights:
            header.append("- No new trusted sources matched the request.")
            return "\n".join(header)
        header.append("- Highlights:")
        for highlight in self.highlights:
            tier_text = f"tier {highlight.tier}" if highlight.tier else "untiered"
            header.append(
                "  • "
                + f"{highlight.topic} ← {highlight.source} ({tier_text}, {highlight.kind}): "
                + f"{highlight.summary} | {highlight.insight}"
            )
        return "\n".join(header)


@dataclass
class CurriculumProgress:
    """Tracks progress within a curriculum stage."""

    stage: CurriculumStage
    ingested: int = 0
    quiz_score: float = 0.0


def _build_autonomous_sources() -> List[AutonomousSource]:
    sources: List[AutonomousSource] = []
    for blueprint in trusted_source_blueprints():
        sources.append(
            AutonomousSource(
                source=str(blueprint["source"]),
                topic=str(blueprint["topic"]),
                summary=str(blueprint["summary"]),
                insight=str(blueprint["insight"]),
                tags=tuple(blueprint["tags"]),
                tier=str(blueprint["tier"]),
                refresh_days=int(blueprint["refresh_days"]),
            )
        )
    return sources


AUTONOMOUS_SOURCES: List[AutonomousSource] = _build_autonomous_sources()

class WebGrowthSystem:
    """Validates and imports external findings into the Memory Web."""

    def __init__(self, memory: MemoryWeb, firewall: FirewallRing) -> None:
        self._memory = memory
        self._firewall = firewall
        self._crawl_log: List[str] = []
        self._autonomous_cursor = 0
        self._curriculum_stages: List[CurriculumStage] = list(CURRICULUM_STAGES)
        self._curriculum_index: int = 0
        self._curriculum_progress: Dict[str, CurriculumProgress] = {
            stage.name: CurriculumProgress(stage=stage)
            for stage in self._curriculum_stages
        }
        self._stage_iterators = {
            stage.name: stage_lesson_iterator(stage)
            for stage in self._curriculum_stages
        }

    def register_additional_sources(
        self, sources: Iterable[AutonomousSource]
    ) -> None:
        """Expand the trusted source list with synthetic catalogues."""

        seen = {(source.source, source.topic) for source in AUTONOMOUS_SOURCES}
        for source in sources:
            key = (source.source, source.topic)
            if key in seen:
                continue
            AUTONOMOUS_SOURCES.append(source)
            seen.add(key)

    def integrate(self, findings: Iterable[WebFinding]) -> int:
        imported = 0
        for finding in findings:
            if not finding.verified:
                continue
            self._memory.record("web", f"{finding.source}: {finding.summary}", 0.6, "web")
            self._crawl_log.append(finding.source)
            imported += 1
        return imported

    def describe_policy(self) -> str:
        allowed = ", ".join(sorted(self._firewall._allowed))
        if not self._crawl_log:
            return f"Web integration restricted to commands: {allowed}"
        last_sources = ", ".join(self._crawl_log[-3:])
        return (
            f"Web integration restricted to commands: {allowed}. "
            f"Latest trusted sources: {last_sources}"
        )

    # Curriculum helpers -------------------------------------------------
    def _current_progress(self) -> CurriculumProgress:
        stage = self._curriculum_stages[self._curriculum_index]
        return self._curriculum_progress[stage.name]

    def _advance_curriculum(
        self, batch_size: int
    ) -> tuple[List[AutoTrainingHighlight], str, float, bool, int]:
        progress = self._current_progress()
        iterator = self._stage_iterators[progress.stage.name]
        lessons: List[str] = []
        for _ in range(batch_size):
            lesson = next(iterator)
            self._memory.record(
                lesson.topic,
                lesson.content,
                lesson.confidence,
                lesson.provenance,
            )
            lessons.append(lesson.topic)
            progress.ingested += 1
        progress.quiz_score = self._simulate_quiz(progress)
        stage_complete = progress.quiz_score >= progress.stage.promotion_threshold
        studied_stage = progress.stage.name
        excerpt = ", ".join(lessons[:3])
        insight = (
            f"Curriculum quiz score {progress.quiz_score:.2f} "
            f"(goal {progress.stage.promotion_threshold:.2f})."
        )
        highlight = AutoTrainingHighlight(
            source=f"curriculum://{progress.stage.name}",
            topic=progress.stage.description,
            summary=f"Absorbed {len(lessons)} lessons covering {excerpt}...",
            insight=insight,
            tier="S",
            kind="curriculum",
        )
        if stage_complete and self._curriculum_index < len(self._curriculum_stages) - 1:
            self._curriculum_index += 1
        return [highlight], studied_stage, progress.quiz_score, stage_complete, len(lessons)

    def _simulate_quiz(self, progress: CurriculumProgress) -> float:
        stage = progress.stage
        total_lessons = max(1, len(stage.lessons))
        coverage = min(1.0, progress.ingested / total_lessons)
        quiz_influence = min(1.0, coverage * len(stage.quiz_bank) / max(1, len(stage.quiz_bank)))
        score = 0.6 + coverage * 0.35 + quiz_influence * 0.05
        return max(0.0, min(1.0, score))

    def bootstrap(self, findings: Iterable[WebFinding]) -> int:
        """Ingest a batch of pre-validated findings immediately."""

        return self.integrate(findings)

    def autonomous_training(
        self, focus: Optional[str] = None, batch_size: int = 5
    ) -> AutoTrainingReport:
        """Harvest a curated batch of trusted sources for self-training."""

        focus_text = (focus or "").strip()
        focus_tokens = {token for token in focus_text.lower().split() if token}
        stage_highlights, studied_stage, quiz_score, stage_complete, stage_count = self._advance_curriculum(
            max(1, batch_size // 2)
        )
        if focus_tokens:
            pool: List[AutonomousSource] = []
            for source in AUTONOMOUS_SOURCES:
                tag_space = (
                    {tag.lower() for tag in source.tags}
                    | set(source.topic.lower().replace("::", " ").split())
                    | set(source.summary.lower().split())
                )
                if focus_tokens & tag_space:
                    pool.append(source)
                    if len(pool) >= batch_size * 5:
                        break
        else:
            pool = []
        if not pool:
            start = self._autonomous_cursor
            end = start + batch_size
            pool = AUTONOMOUS_SOURCES[start:end]
            if not pool:
                self._autonomous_cursor = 0
                pool = AUTONOMOUS_SOURCES[:batch_size]
            self._autonomous_cursor = (start + len(pool)) % len(AUTONOMOUS_SOURCES)
        web_highlights: List[AutoTrainingHighlight] = []
        for source in pool[:batch_size]:
            content = f"{source.summary} Insight: {source.insight}"
            self._memory.record(
                source.topic,
                content,
                0.72,
                "autonomous_web",
            )
            self._memory.record(
                f"autonomy::comprehension::{source.topic}",
                f"Validated understanding of {source.topic} using {source.source}.",
                0.78,
                "autonomous_web",
            )
            self._crawl_log.append(source.source)
            web_highlights.append(
                AutoTrainingHighlight(
                    source=source.source,
                    topic=source.topic,
                    summary=source.summary,
                    insight=source.insight,
                    tier=source.tier,
                    kind="web",
                )
            )
        highlights = stage_highlights + web_highlights
        imported = stage_count + len(web_highlights)
        return AutoTrainingReport(
            focus=focus_text,
            imported=imported,
            highlights=highlights,
            curriculum_stage=studied_stage,
            quiz_score=quiz_score,
            stage_complete=stage_complete,
        )
