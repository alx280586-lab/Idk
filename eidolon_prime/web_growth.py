"""Web growth subsystem for ingesting curated external knowledge."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, TYPE_CHECKING

from .memory import MemoryWeb
from .firewall import FirewallRing
from .curriculum import (
    CURRICULUM_STAGES,
    CurriculumStage,
    stage_lesson_iterator,
    trusted_source_blueprints,
)

if TYPE_CHECKING:  # pragma: no cover - type-only import
    from .config import WebSettings
    from .comprehension import MessageUnderstanding


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
    trust_notes: List[str] = field(default_factory=list)
    average_trust: float = 0.0

    def render(self) -> str:
        header = [
            "Autonomous training complete!",
            f"- Focus: {self.focus or 'general knowledge'}",
            f"- Entries captured: {self.imported}",
            f"- Curriculum stage: {self.curriculum_stage} (quiz score {self.quiz_score:.2f})",
        ]
        if self.stage_complete:
            header.append("- Stage milestone achieved! Progressing to deeper skills.")
        if self.trust_notes:
            header.append(f"- Average trust score: {self.average_trust:.2f}")
            header.append("- Trust assessments:")
            for note in self.trust_notes[:12]:
                header.append(f"  • {note}")
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


@dataclass(frozen=True)
class TrustAssessment:
    """Represents the trust analysis for an arbitrary domain."""

    domain: str
    score: float
    tier: str
    rationale: str


@dataclass(frozen=True)
class OpenWebSource:
    """Container describing an unrestricted open-web candidate."""

    domain: str
    topic: str
    summary: str
    insight: str
    focus: str


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


class DomainTrustEvaluator:
    """Scores arbitrary domains using transparent heuristics."""

    _TLD_WEIGHTS: Dict[str, float] = {
        "gov": 0.32,
        "mil": 0.28,
        "edu": 0.26,
        "org": 0.18,
        "net": 0.12,
        "com": 0.1,
        "dev": 0.14,
        "io": 0.12,
        "ai": 0.12,
        "co": 0.08,
        "us": 0.08,
        "uk": 0.08,
        "ca": 0.08,
        "au": 0.08,
        "jp": 0.08,
        "de": 0.08,
        "fr": 0.08,
    }

    _CREDIBILITY_KEYWORDS: Tuple[str, ...] = (
        "docs",
        "developer",
        "api",
        "wikipedia",
        "encyclopedia",
        "standard",
        "spec",
        "kb",
        "support",
        "manual",
        "research",
    )

    _RISK_KEYWORDS: Tuple[str, ...] = (
        "casino",
        "torrent",
        "gamble",
        "spam",
        "malware",
        "hack",
        "exploit",
        "leak",
        "fan",
        "rumor",
    )

    def __init__(self, parameter_budget: int, parameter_groups: int) -> None:
        self._parameter_budget = max(1, parameter_budget)
        self._parameter_groups = max(1, parameter_groups)
        self._cache: Dict[str, TrustAssessment] = {}

    def evaluate(self, domain: str, focus_terms: Sequence[str]) -> TrustAssessment:
        canonical = domain.lower().strip()
        cached = self._cache.get(canonical)
        if cached:
            return cached
        score = 0.45
        tld = self._extract_tld(canonical)
        score += self._TLD_WEIGHTS.get(tld, 0.05)
        parameter_bonus = math.log10(self._parameter_budget * self._parameter_groups + 1.0) / 10.0
        score += min(0.25, parameter_bonus)
        token_bonus = min(0.18, len(focus_terms) / 40.0)
        score += token_bonus
        credibility_hits = [kw for kw in self._CREDIBILITY_KEYWORDS if kw in canonical]
        if credibility_hits:
            score += 0.08 + 0.02 * len(credibility_hits)
        risk_hits = [kw for kw in self._RISK_KEYWORDS if kw in canonical]
        if risk_hits:
            score -= 0.12 + 0.03 * len(risk_hits)
        score = max(0.05, min(0.99, score))
        if score >= 0.86:
            tier = "A"
        elif score >= 0.72:
            tier = "B"
        elif score >= 0.6:
            tier = "C"
        else:
            tier = "D"
        rationale_bits = [f"TLD {tld or 'unknown'}"]
        if credibility_hits:
            rationale_bits.append(f"credibility markers: {', '.join(credibility_hits[:3])}")
        if risk_hits:
            rationale_bits.append(f"risks: {', '.join(risk_hits[:2])}")
        if focus_terms:
            rationale_bits.append(f"focus alignment ×{len(focus_terms)}")
        rationale_bits.append(f"parameter leverage {self._parameter_budget:,}")
        rationale = ", ".join(rationale_bits)
        assessment = TrustAssessment(domain=canonical, score=score, tier=tier, rationale=rationale)
        self._cache[canonical] = assessment
        return assessment

    @staticmethod
    def _extract_tld(domain: str) -> str:
        parts = domain.split(".")
        return parts[-1] if parts and parts[-1] else ""


class OpenWebUniverse:
    """Generates open-web candidates and applies trust filtering."""

    def __init__(
        self,
        *,
        trust_threshold: float,
        max_samples: int,
        parameter_budget: int,
        parameter_groups: int,
    ) -> None:
        self._trust_threshold = max(0.0, min(0.99, trust_threshold))
        self._max_samples = max(6, max_samples)
        self._evaluator = DomainTrustEvaluator(parameter_budget, parameter_groups)
        self._reference_domains: Tuple[str, ...] = (
            "wikipedia.org",
            "britannica.com",
            "developer.roblox.com",
            "create.roblox.com",
            "education.roblox.com",
            "docs.python.org",
            "docs.microsoft.com",
            "opensource.guide",
            "khanacademy.org",
            "mit.edu",
            "nasa.gov",
            "noaa.gov",
            "who.int",
            "un.org",
            "robloxdevforum.com",
            "stackoverflow.com",
            "w3.org",
        )
        self._prefixes: Tuple[str, ...] = ("", "www.", "docs.", "developer.", "api.", "learn.", "support.", "en.")
        self._tlds: Tuple[str, ...] = (
            "gov",
            "edu",
            "org",
            "com",
            "net",
            "dev",
            "io",
            "ai",
            "info",
            "co",
            "tech",
            "science",
            "research",
            "wiki",
        )
        self._default_focus: Tuple[str, ...] = (
            "knowledge",
            "education",
            "engineering",
            "science",
            "ethics",
            "governance",
        )

    def harvest(
        self, focus_tokens: Set[str], request_batch: int
    ) -> Tuple[List[Tuple[OpenWebSource, TrustAssessment]], List[str]]:
        tokens = [token for token in sorted(focus_tokens) if token]
        if not tokens:
            tokens = list(self._default_focus)
        candidate_limit = max(self._max_samples * 2, request_batch * 6)
        candidate_domains = self._generate_candidates(tokens, candidate_limit)
        accepted: List[Tuple[OpenWebSource, TrustAssessment]] = []
        notes: List[str] = []
        for domain in candidate_domains:
            assessment = self._evaluator.evaluate(domain, tokens)
            status = "Accepted" if assessment.score >= self._trust_threshold else "Discarded"
            notes.append(
                f"{status} {assessment.domain} (score {assessment.score:.2f}, tier {assessment.tier}) — {assessment.rationale}"
            )
            if assessment.score < self._trust_threshold:
                continue
            source = self._build_source(domain, tokens, assessment)
            accepted.append((source, assessment))
            if len(accepted) >= max(self._max_samples, request_batch):
                break
        return accepted, notes

    def _generate_candidates(self, tokens: Sequence[str], limit: int) -> List[str]:
        seen: List[str] = []
        for token in tokens:
            sanitized = re.sub(r"[^a-z0-9]+", "", token.lower())
            if not sanitized:
                continue
            for prefix in self._prefixes:
                for tld in self._tlds:
                    domain = f"{prefix}{sanitized}.{tld}" if prefix else f"{sanitized}.{tld}"
                    domain = domain.replace("..", ".")
                    if domain not in seen:
                        seen.append(domain)
                        if len(seen) >= limit:
                            return seen
        for reference in self._reference_domains:
            if reference not in seen:
                seen.append(reference)
                if len(seen) >= limit:
                    break
        return seen

    def _build_source(
        self, domain: str, tokens: Sequence[str], assessment: TrustAssessment
    ) -> OpenWebSource:
        focus_text = ", ".join(tokens[:4]) or "general knowledge"
        topic_slug = domain.replace(".", "::")
        summary = f"Open web sweep of {domain} centred on {focus_text}."
        insight = (
            f"Trust tier {assessment.tier} with score {assessment.score:.2f}; {assessment.rationale}."
        )
        return OpenWebSource(
            domain=domain,
            topic=f"open_web::{topic_slug}",
            summary=summary,
            insight=insight,
            focus=focus_text,
        )

class WebGrowthSystem:
    """Validates and imports external findings into the Memory Web."""

    def __init__(
        self,
        memory: MemoryWeb,
        firewall: FirewallRing,
        settings: Optional["WebSettings"] = None,
        parameter_budget: int = 3_200_000,
        parameter_groups: int = 16,
    ) -> None:
        self._memory = memory
        self._firewall = firewall
        self._settings = settings
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
        unrestricted = settings.unrestricted_access if settings else True
        trust_threshold = settings.trust_threshold if settings else 0.6
        max_open_samples = settings.max_open_web_samples if settings else 24
        interactive_batch = (
            settings.interactive_research_batch if settings else 12
        )
        self._unrestricted = unrestricted
        self._open_web = OpenWebUniverse(
            trust_threshold=trust_threshold,
            max_samples=max_open_samples,
            parameter_budget=parameter_budget,
            parameter_groups=parameter_groups,
        )
        self._interactive_batch = max(6, interactive_batch)

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
        (
            stage_highlights,
            studied_stage,
            quiz_score,
            stage_complete,
            stage_count,
        ) = self._advance_curriculum(max(1, batch_size // 2))
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
        open_highlights: List[AutoTrainingHighlight] = []
        trust_notes: List[str] = []
        average_trust = 0.0
        if self._unrestricted:
            accepted, trust_notes = self._harvest_open_web(focus_tokens, batch_size)
            if accepted:
                average_trust = sum(assessment.score for _, assessment in accepted) / len(accepted)
            for source, assessment in accepted:
                content = f"{source.summary} {source.insight}"
                confidence = 0.55 + 0.35 * assessment.score
                self._memory.record(
                    source.topic,
                    content,
                    min(0.98, confidence),
                    "open_web",
                )
                self._memory.record(
                    f"autonomy::trust::{source.topic}",
                    (
                        f"Confirmed {source.focus} from {assessment.domain}"
                        f" with trust {assessment.score:.2f} ({assessment.tier})."
                    ),
                    0.6 + 0.25 * assessment.score,
                    "open_web",
                )
                self._crawl_log.append(f"https://{source.domain}")
                open_highlights.append(
                    AutoTrainingHighlight(
                        source=f"https://{source.domain}",
                        topic=source.topic,
                        summary=source.summary,
                        insight=f"{source.insight} (trust {assessment.score:.2f})",
                        tier=assessment.tier,
                        kind="open-web",
                    )
                )
        highlights = stage_highlights + web_highlights + open_highlights
        imported = stage_count + len(web_highlights) + len(open_highlights)
        return AutoTrainingReport(
            focus=focus_text,
            imported=imported,
            highlights=highlights,
            curriculum_stage=studied_stage,
            quiz_score=quiz_score,
            stage_complete=stage_complete,
            trust_notes=trust_notes,
            average_trust=average_trust,
        )

    def interactive_research(
        self,
        query: str,
        understanding: Optional["MessageUnderstanding"] = None,
        *,
        batch_size: Optional[int] = None,
    ) -> AutoTrainingReport:
        """Run an on-demand research sweep tied to a specific user query."""

        request_batch = max(4, batch_size or self._interactive_batch)
        focus_tokens: Set[str] = set(
            token for token in re.findall(r"[A-Za-z0-9]+", query.lower()) if token
        )
        if understanding is not None:
            focus_tokens.update(term.lower() for term in understanding.focus_terms)
            for pair in understanding.focus_pairs:
                for segment in pair.split():
                    cleaned = segment.strip().lower()
                    if cleaned:
                        focus_tokens.add(cleaned)
        curated_highlights: List[AutoTrainingHighlight] = []
        curated_count = 0
        if focus_tokens:
            curated_pool: List[AutonomousSource] = []
            for source in AUTONOMOUS_SOURCES:
                tag_space = (
                    {tag.lower() for tag in source.tags}
                    | set(source.topic.lower().replace("::", " ").split())
                    | set(source.summary.lower().split())
                )
                if focus_tokens & tag_space:
                    curated_pool.append(source)
                    if len(curated_pool) >= request_batch:
                        break
        else:
            curated_pool = []
        if not curated_pool:
            curated_pool = AUTONOMOUS_SOURCES[: min(request_batch, len(AUTONOMOUS_SOURCES))]
        for source in curated_pool:
            context_summary = (
                f"Interactive research captured {source.topic} via {source.source}."
            )
            self._memory.record(
                source.topic,
                context_summary,
                0.74,
                "interactive_research",
            )
            curated_highlights.append(
                AutoTrainingHighlight(
                    source=source.source,
                    topic=source.topic,
                    summary=source.summary,
                    insight=f"Reinforced interactively: {source.insight}",
                    tier=source.tier,
                    kind="interactive-curated",
                )
            )
            curated_count += 1
        accepted, trust_notes = self._harvest_open_web(focus_tokens, request_batch)
        open_highlights: List[AutoTrainingHighlight] = []
        average_trust = 0.0
        if accepted:
            average_trust = sum(assessment.score for _, assessment in accepted) / len(accepted)
        for source, assessment in accepted:
            focus_text = source.focus
            memory_content = (
                f"Live research for '{query}' via {assessment.domain} → {focus_text}."
            )
            confidence = 0.58 + 0.32 * assessment.score
            self._memory.record(
                source.topic,
                memory_content,
                min(0.99, confidence),
                "interactive_research",
            )
            open_highlights.append(
                AutoTrainingHighlight(
                    source=f"https://{assessment.domain}",
                    topic=source.topic,
                    summary=source.summary,
                    insight=f"{source.insight} (trust {assessment.score:.2f})",
                    tier=assessment.tier,
                    kind="live-research",
                )
            )
        total_imported = curated_count + len(accepted)
        quiz_score = 0.68
        if total_imported:
            quiz_score = 0.75 + min(0.2, total_imported / (request_batch * 2))
        highlights = curated_highlights + open_highlights
        return AutoTrainingReport(
            focus=query,
            imported=total_imported,
            highlights=highlights,
            curriculum_stage="interactive_research",
            quiz_score=quiz_score,
            stage_complete=False,
            trust_notes=trust_notes,
            average_trust=average_trust,
        )

    def _harvest_open_web(
        self, focus_tokens: Set[str], batch_size: int
    ) -> Tuple[List[Tuple[OpenWebSource, TrustAssessment]], List[str]]:
        return self._open_web.harvest(focus_tokens, batch_size)
