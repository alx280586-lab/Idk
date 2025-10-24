"""Kernel orchestrates engine components."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Iterable

from .config import EidolonConfig
from .state import PersonalityState
from .cortex import Cortex, CortexResult, AgentResponse
from .memory import MemoryWeb, MemoryEntry
from .forge import Forge
from .firewall import FirewallRing
from .reflection import ReflectionEngine
from .training import TrainingGround, TrainingRecord
from .web_growth import WebGrowthSystem, WebFinding
from .dataset import load_seed_training_corpus


@dataclass
class ChatResult:
    """Response object returned by conversational turns."""

    prompt: str
    reply: str
    analysis: CortexResult

    def render(self) -> str:
        lines = ["Eidolon Prime:"]
        lines.append(self.reply)
        lines.append("\nAnalysis trace:")
        lines.append(self.analysis.render())
        return "\n".join(lines)


@dataclass
class KernelStatus:
    """Snapshot of the current system state."""

    resources: Dict[str, Any]
    personality: str
    memory_stats: Dict[str, int]


class Kernel:
    """Coordinates the major subsystems."""

    def __init__(
        self,
        config: EidolonConfig,
        cortex: Cortex,
        personality: PersonalityState,
        memory: MemoryWeb,
        forge: Forge,
        firewall: FirewallRing,
        reflection: ReflectionEngine,
        training: TrainingGround,
        web_growth: WebGrowthSystem,
    ) -> None:
        self._config = config
        self._cortex = cortex
        self._personality = personality
        self._memory = memory
        self._forge = forge
        self._firewall = firewall
        self._reflection = reflection
        self._training = training
        self._web_growth = web_growth
        self._autonomy_initialized = False
        self._seed_initialized = False

    def process_request(self, prompt: str) -> CortexResult:
        return self._cortex.process(prompt)

    def status(self) -> KernelStatus:
        resources = {
            "compute_budget": self._config.resources.compute_budget,
            "max_parallel_agents": self._config.resources.max_parallel_agents,
            "experiment_limit": self._config.resources.experiment_limit,
        }
        return KernelStatus(resources, self._personality.describe(), self._memory.summarize())

    def permits_command(self, command: str) -> bool:
        return self._firewall.permits(command)

    def train(self, payload: str) -> TrainingRecord:
        self._firewall.inspect("train", payload)
        record = self._training.ingest(payload)
        self._personality.adjust(confidence=0.01, curiosity=0.02)
        return record

    def chat(self, message: str) -> ChatResult:
        self._firewall.inspect("talk", message)
        analysis = self._cortex.process(message)
        tone = self._describe_tone()
        reasoning_summary = analysis.reasoning_summary
        strategic_notes = self._summarize_insights(analysis.responses)
        evidence_block = self._format_evidence(analysis.related_memories)
        reply = (
            f"{tone}\n"
            f"Prompt understood as: {message}\n"
            f"Reasoning summary: {reasoning_summary}\n"
            f"Strategic notes: {strategic_notes}\n"
            f"Evidence I'm weighing:\n{evidence_block}"
        )
        self._memory.record("conversation", f"user::{message}", 0.6, "collaboration")
        self._memory.record("conversation", f"eidolon::{reply}", 0.65, "collaboration")
        return ChatResult(message, reply, analysis)

    def _summarize_insights(self, responses: Iterable[AgentResponse]) -> str:
        highlights = []
        for response in responses:
            if response.agent in {"logic", "curiosity", "reasoning"}:
                highlights.append(response.insight)
            if len(highlights) >= 3:
                break
        if not highlights:
            return "Still collecting evidence before committing to a direction."
        return " | ".join(highlights)

    def _format_evidence(self, memories: Iterable[MemoryEntry]) -> str:
        evidence_lines = []
        for entry in list(memories)[:4]:
            domain, _, aspect = entry.topic.partition("::")
            if "so that the initiative " in entry.content:
                benefit = entry.content.split("so that the initiative ", 1)[1].rstrip(".")
            else:
                benefit = "produces consistent improvements"
            evidence_lines.append(
                f"- {domain.title()} emphasises {aspect} to ensure it {benefit}."
            )
        if not evidence_lines:
            evidence_lines.append("- No matching memories yet; please share more training input when ready.")
        return "\n".join(evidence_lines)

    def enforce_security(self, command: str, payload: str) -> None:
        self._firewall.inspect(command, payload)

    def bootstrap(self) -> None:
        """Auto-ingest trusted web knowledge once per engine lifetime."""

        if self._autonomy_initialized:
            return

        if not self._seed_initialized:
            seeded = load_seed_training_corpus(self._memory)
            if seeded:
                self._personality.adjust(confidence=0.08, curiosity=0.05, integrity=0.03)
            self._seed_initialized = True
        settings = self._config.web
        if not settings.autostart:
            self._autonomy_initialized = True
            return
        findings = []
        for seed in settings.seeds:
            findings.append(
                WebFinding(source=seed.url, summary=seed.summary, verified=True)
            )
        imported = self._web_growth.bootstrap(findings)
        if imported:
            self._personality.adjust(curiosity=0.05, confidence=0.02)
        self._autonomy_initialized = True

    def _describe_tone(self) -> str:
        if self._personality.empathy > 0.7:
            return "I'm feeling especially supportive."
        if self._personality.curiosity > 0.6:
            return "Curiosity is high, so let's explore together."
        if self._personality.confidence < 0.4:
            return "I'll take a careful approach."
        return "Here's my considered response."
