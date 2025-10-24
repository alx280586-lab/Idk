"""Web growth subsystem for ingesting curated external knowledge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from .memory import MemoryWeb
from .firewall import FirewallRing


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


@dataclass
class AutoTrainingHighlight:
    """Key points surfaced during an autonomous training cycle."""

    source: str
    topic: str
    insight: str


@dataclass
class AutoTrainingReport:
    """Telemetry returned after crawling trusted domains."""

    focus: str
    imported: int
    highlights: List[AutoTrainingHighlight]

    def render(self) -> str:
        header = [
            "Autonomous training complete!",
            f"- Focus: {self.focus or 'general knowledge'}",
            f"- Entries captured: {self.imported}",
        ]
        if not self.highlights:
            header.append("- No new trusted sources matched the request.")
            return "\n".join(header)
        header.append("- Highlights:")
        for highlight in self.highlights:
            header.append(
                f"  • {highlight.topic} ← {highlight.source}: {highlight.insight}"
            )
        return "\n".join(header)


AUTONOMOUS_SOURCES: List[AutonomousSource] = [
    AutonomousSource(
        source="https://create.roblox.com/docs/production/iterative-development",
        topic="roblox::experience_iteration",
        summary="Roblox Developer Hub guidance on rapid playtesting and telemetry-led adjustments.",
        insight=(
            "Successful Roblox experiences schedule weekly playtests and pair analytics with player"
            " interviews to keep updates grounded in actual community behavior."
        ),
        tags=("roblox", "game design", "analytics"),
    ),
    AutonomousSource(
        source="https://education.roblox.com/en-us/resources/curriculum",
        topic="roblox::learning_curriculum",
        summary="Roblox Education curriculum emphasising creative coding for newcomers.",
        insight=(
            "Curriculum modules scaffold Lua fundamentals with hands-on building challenges so"
            " aspiring developers connect syntax to outcomes."
        ),
        tags=("roblox", "education", "lua"),
    ),
    AutonomousSource(
        source="https://devforum.roblox.com/",
        topic="roblox::community_best_practices",
        summary="Roblox DevForum discussions curated for deployment and moderation lessons.",
        insight=(
            "Seasoned creators log incident retrospectives that emphasise automated moderation hooks"
            " and rollback scripts before shipping live updates."
        ),
        tags=("roblox", "operations", "moderation"),
    ),
    AutonomousSource(
        source="https://developer.roblox.com/articles/economy-design",
        topic="roblox::economy_design",
        summary="Economic design blueprint from Roblox documentation.",
        insight=(
            "Stable experience economies cap premium currency sinks, test pricing with A/B cohorts,"
            " and pair rewards with skill-building loops to avoid pay-to-win drift."
        ),
        tags=("roblox", "economy", "design"),
    ),
    AutonomousSource(
        source="https://developer.mozilla.org/en-US/docs/Learn",
        topic="web_dev::fundamentals",
        summary="Mozilla Developer Network learn web development pathway.",
        insight=(
            "Building resilient web apps starts with semantic HTML, progressive enhancement, and"
            " automated accessibility testing baked into the CI pipeline."
        ),
        tags=("coding", "web", "accessibility"),
    ),
    AutonomousSource(
        source="https://docs.github.com/en/get-started/quickstart",
        topic="software_practice::version_control",
        summary="GitHub quickstart on collaborative workflows.",
        insight=(
            "Teams thrive when every change flows through pull requests with status checks, review"
            " gates, and a documented rollback strategy."
        ),
        tags=("coding", "git", "collaboration"),
    ),
    AutonomousSource(
        source="https://stackoverflow.com/help/how-to-ask",
        topic="community::knowledge_sharing",
        summary="Stack Overflow best practices for effective questions.",
        insight=(
            "Precise reproduction steps and minimal code samples accelerate peer support and build"
            " reusable knowledge assets."
        ),
        tags=("coding", "communication", "community"),
    ),
    AutonomousSource(
        source="https://martinfowler.com/bliki/ContinuousDelivery.html",
        topic="software_practice::continuous_delivery",
        summary="Martin Fowler essay on Continuous Delivery fundamentals.",
        insight=(
            "Continuous delivery keeps deploys boring by automating verification, feature flag rollouts,"
            " and post-release monitoring."
        ),
        tags=("coding", "devops", "delivery"),
    ),
    AutonomousSource(
        source="https://en.wikipedia.org/wiki/Systems_thinking",
        topic="encyclopedia::systems_thinking",
        summary="Wikipedia overview of systems thinking concepts and feedback loops.",
        insight=(
            "Balancing and reinforcing feedback loops explain why interventions can produce"
            " counter-intuitive outcomes without holistic diagnostics."
        ),
        tags=("encyclopedia", "systems", "theory"),
    ),
    AutonomousSource(
        source="https://en.wikipedia.org/wiki/Software_engineering",
        topic="encyclopedia::software_engineering",
        summary="Wikipedia entry on software engineering disciplines.",
        insight=(
            "Software engineering blends requirements analysis, design, coding, testing, and"
            " maintenance into an iterative lifecycle guided by quality metrics."
        ),
        tags=("encyclopedia", "software", "engineering"),
    ),
    AutonomousSource(
        source="https://www.britannica.com/science/artificial-intelligence",
        topic="encyclopedia::artificial_intelligence",
        summary="Encyclopedia Britannica article on AI foundations and history.",
        insight=(
            "Classical AI emphasises symbolic reasoning while modern approaches combine data-driven"
            " learning with knowledge-based safeguards."
        ),
        tags=("encyclopedia", "ai", "history"),
    ),
    AutonomousSource(
        source="https://www.britannica.com/topic/encyclopaedia",
        topic="encyclopedia::knowledge_preservation",
        summary="Britannica insight into the role of encyclopedias.",
        insight=(
            "Encyclopedias curate verified knowledge to provide context and citations that reinforce"
            " intellectual integrity."
        ),
        tags=("encyclopedia", "knowledge", "reference"),
    ),
]


class WebGrowthSystem:
    """Validates and imports external findings into the Memory Web."""

    def __init__(self, memory: MemoryWeb, firewall: FirewallRing) -> None:
        self._memory = memory
        self._firewall = firewall
        self._crawl_log: List[str] = []
        self._autonomous_cursor = 0

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

    def bootstrap(self, findings: Iterable[WebFinding]) -> int:
        """Ingest a batch of pre-validated findings immediately."""

        return self.integrate(findings)

    def autonomous_training(
        self, focus: Optional[str] = None, batch_size: int = 5
    ) -> AutoTrainingReport:
        """Harvest a curated batch of trusted sources for self-training."""

        focus_text = (focus or "").strip()
        focus_tokens = {token for token in focus_text.lower().split() if token}
        if focus_tokens:
            pool = [
                source
                for source in AUTONOMOUS_SOURCES
                if focus_tokens
                & (
                    {tag.lower() for tag in source.tags}
                    | set(source.topic.lower().split("::"))
                    | set(source.summary.lower().split())
                )
            ]
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
        highlights: List[AutoTrainingHighlight] = []
        for source in pool[:batch_size]:
            content = f"{source.summary} Insight: {source.insight}"
            self._memory.record(
                source.topic,
                content,
                0.72,
                "autonomous_web",
            )
            self._crawl_log.append(source.source)
            highlights.append(
                AutoTrainingHighlight(
                    source=source.source,
                    topic=source.topic,
                    insight=source.insight,
                )
            )
        return AutoTrainingReport(focus=focus_text, imported=len(highlights), highlights=highlights)
