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
    AutonomousSource(
        source="https://create.roblox.com/docs/luau/style-guide",
        topic="roblox::luau_style",
        summary="Roblox Luau style guide encouraging readable scripting conventions.",
        insight=(
            "Readable Roblox code favors descriptive variable names, module boundaries, and"
            " consistent service access patterns to make collaboration smoother."
        ),
        tags=("roblox", "coding", "style"),
    ),
    AutonomousSource(
        source="https://create.roblox.com/docs/production/polish/optimization",
        topic="roblox::performance_tuning",
        summary="Roblox optimization handbook for keeping experiences fast across devices.",
        insight=(
            "Profiling scripts, throttling expensive loops, and streaming assets lazily prevent"
            " frame drops on lower-end hardware."
        ),
        tags=("roblox", "performance", "optimization"),
    ),
    AutonomousSource(
        source="https://create.roblox.com/docs/reference/engine/classes/DataStoreService",
        topic="roblox::data_persistence",
        summary="DataStoreService documentation for durable Roblox experience state.",
        insight=(
            "Data stores demand retry logic, budget awareness, and serialization hygiene so"
            " players never lose progress."
        ),
        tags=("roblox", "data", "architecture"),
    ),
    AutonomousSource(
        source="https://learn.roblox.com/en-us/creator-analytics",
        topic="roblox::analytics",
        summary="Roblox creator analytics overview for measuring experience health.",
        insight=(
            "Tracking retention, session length, and funnel drop-offs guides experiments that"
            " actually improve playtime."
        ),
        tags=("roblox", "analytics", "metrics"),
    ),
    AutonomousSource(
        source="https://create.roblox.com/docs/production/publishing/peer-review",
        topic="roblox::safety_review",
        summary="Roblox peer review process for moderated publishing.",
        insight=(
            "Roblox peer review enforces community standards by requiring human verification"
            " before large updates go live."
        ),
        tags=("roblox", "safety", "moderation"),
    ),
    AutonomousSource(
        source="https://docs.python.org/3/tutorial/index.html",
        topic="coding::python_tutorial",
        summary="Python official tutorial detailing idiomatic language patterns.",
        insight=(
            "Python encourages readable modules, batteries-included libraries, and exception"
            " driven control flow for clarity."
        ),
        tags=("coding", "python", "tutorial"),
    ),
    AutonomousSource(
        source="https://go.dev/doc/effective_go",
        topic="coding::effective_go",
        summary="Effective Go guidance on idiomatic Go design decisions.",
        insight=(
            "Idiomatic Go leans on composition, small interfaces, and goroutines guarded by"
            " channels for concurrency."
        ),
        tags=("coding", "go", "style"),
    ),
    AutonomousSource(
        source="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        topic="web_dev::javascript_guide",
        summary="MDN's canonical JavaScript guide covering language features and best practices.",
        insight=(
            "Understanding closures, prototypes, and event loops enables responsive web"
            " interactions without race conditions."
        ),
        tags=("coding", "javascript", "web"),
    ),
    AutonomousSource(
        source="https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA",
        topic="web_dev::accessibility_aria",
        summary="MDN ARIA authoring practices for inclusive interfaces.",
        insight=(
            "Landmark roles and labelled controls make complex widgets screen-reader friendly"
            " without compromising interactivity."
        ),
        tags=("web", "accessibility", "standards"),
    ),
    AutonomousSource(
        source="https://12factor.net/",
        topic="software_practice::twelve_factor",
        summary="The Twelve-Factor App methodology for resilient services.",
        insight=(
            "Strict separation of config, stateless processes, and fast startup reduces"
            " deployment surprises in distributed systems."
        ),
        tags=("software", "architecture", "cloud"),
    ),
    AutonomousSource(
        source="https://docs.github.com/en/actions",
        topic="software_practice::github_actions",
        summary="GitHub Actions documentation for automation workflows.",
        insight=(
            "CI pipelines stay reliable when steps are modular, cached artifacts are reused,"
            " and secrets stay encrypted."
        ),
        tags=("devops", "automation", "github"),
    ),
    AutonomousSource(
        source="https://kubernetes.io/docs/concepts/",
        topic="software_practice::kubernetes_concepts",
        summary="Kubernetes core concepts for container orchestration.",
        insight=(
            "Deployments, services, and config maps provide declarative knobs for rolling"
            " updates without downtime."
        ),
        tags=("devops", "kubernetes", "cloud"),
    ),
    AutonomousSource(
        source="https://en.wikipedia.org/wiki/Game_design",
        topic="encyclopedia::game_design",
        summary="Wikipedia overview of game design theory and practice.",
        insight=(
            "Game design blends mechanics, dynamics, and aesthetics so player motivation and"
            " challenge remain balanced."
        ),
        tags=("encyclopedia", "games", "design"),
    ),
    AutonomousSource(
        source="https://www.britannica.com/art/storytelling",
        topic="encyclopedia::storytelling",
        summary="Britannica explanation of storytelling fundamentals.",
        insight=(
            "Effective storytelling establishes stakes, emotional arcs, and resolution to"
            " engage audiences deeply."
        ),
        tags=("encyclopedia", "story", "communication"),
    ),
    AutonomousSource(
        source="https://en.wikipedia.org/wiki/Roblox",
        topic="encyclopedia::roblox_overview",
        summary="Wikipedia article describing Roblox history and platform structure.",
        insight=(
            "Roblox combines user-generated creation tools with social discovery, which is why"
            " community insights matter for long-term success."
        ),
        tags=("encyclopedia", "roblox", "platform"),
    ),
    AutonomousSource(
        source="https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html",
        topic="software_practice::aws_well_architected",
        summary="AWS Well-Architected Framework principles.",
        insight=(
            "Operational excellence, reliability, and cost optimization keep cloud systems"
            " sustainable as they scale."
        ),
        tags=("cloud", "aws", "architecture"),
    ),
    AutonomousSource(
        source="https://refactoring.guru/design-patterns",
        topic="software_practice::design_patterns",
        summary="Catalog of software design patterns from Refactoring Guru.",
        insight=(
            "Patterns like observer, strategy, and builder offer shared vocabulary for"
            " repeatable design problems."
        ),
        tags=("software", "design", "patterns"),
    ),
    AutonomousSource(
        source="https://www.sqlite.org/whentouse.html",
        topic="software_practice::sqlite_guidance",
        summary="SQLite guidance on appropriate usage scenarios.",
        insight=(
            "SQLite shines for embedded and local-first applications while heavier client-server"
            " databases suit concurrent writes."
        ),
        tags=("database", "architecture", "storage"),
    ),
    AutonomousSource(
        source="https://www.postgresql.org/docs/current/",
        topic="software_practice::postgresql_basics",
        summary="PostgreSQL documentation for relational database capabilities.",
        insight=(
            "ACID transactions, advanced indexing, and procedural extensions make PostgreSQL"
            " versatile for data-intensive work."
        ),
        tags=("database", "postgresql", "sql"),
    ),
    AutonomousSource(
        source="https://docs.python.org/3/library/asyncio.html",
        topic="coding::python_asyncio",
        summary="Asyncio documentation covering asynchronous programming in Python.",
        insight=(
            "Event loops and awaitable coroutines let Python services juggle I/O without"
            " blocking threads."
        ),
        tags=("python", "async", "programming"),
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
