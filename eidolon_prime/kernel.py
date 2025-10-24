"""Kernel orchestrates engine components."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, Any, Iterable, Optional

from .config import EidolonConfig
from .state import PersonalityState
from .cortex import Cortex, CortexResult, AgentResponse
from .memory import MemoryWeb, MemoryEntry
from .forge import Forge
from .firewall import FirewallRing
from .reflection import ReflectionEngine
from .training import TrainingGround, TrainingRecord
from .web_growth import WebGrowthSystem, WebFinding, AutoTrainingReport
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


@dataclass
class AutoTrainingStatus:
    """Represents the state of long-running autonomous training."""

    running: bool
    focus: Optional[str]
    message: str

    def render(self) -> str:
        focus_text = self.focus or "general knowledge"
        state = "running" if self.running else "inactive"
        return (
            f"Autonomous training is {state} (focus: {focus_text}).\n"
            f"{self.message}"
        )


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
        self._autonomous_bootstrap_complete = False
        self._continuous_training_thread: Optional[threading.Thread] = None
        self._continuous_training_stop: Optional[threading.Event] = None
        self._continuous_training_focus: Optional[str] = None

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
        intent = self._interpret_intent(message, analysis.related_memories)
        strategic_notes = self._summarize_insights(analysis.responses)
        reasoning_block = self._compose_reasoning_block(analysis)
        evidence_block = self._format_evidence(analysis.related_memories)
        organic_summary = self._compose_reply_summary(
            message,
            analysis.responses,
            strategic_notes,
            analysis.reasoning_summary,
        )
        reply = (
            f"{tone} {intent}\n\n"
            f"Here's the reasoning trail I'm following:\n{reasoning_block}\n\n"
            f"Grounding evidence:\n{evidence_block}\n\n"
            f"Putting it all together: {organic_summary}"
        )
        self._memory.record("conversation", f"user::{message}", 0.6, "collaboration")
        self._memory.record("conversation", f"eidolon::{reply}", 0.65, "collaboration")
        return ChatResult(message, reply, analysis)

    def autonomous_train(
        self, focus: str | None = None, *, batch_size: Optional[int] = None
    ) -> AutoTrainingReport:
        """Trigger a curated crawl across trusted external sources."""

        actual_batch = batch_size or self._config.web.cycle_batch_size
        report = self._web_growth.autonomous_training(focus, batch_size=actual_batch)
        if report.imported:
            self._personality.adjust(curiosity=0.04, confidence=0.02)
        else:
            self._personality.adjust(curiosity=0.01)
        summary_topic = "autonomy::report"
        self._memory.record(summary_topic, report.render(), 0.6, "autonomous_web")
        return report

    def start_autonomous_training(
        self, focus: str | None = None
    ) -> AutoTrainingStatus:
        focus_value = (focus or "").strip() or None
        if self.is_autonomous_training_running():
            return AutoTrainingStatus(
                running=True,
                focus=self._continuous_training_focus,
                message=(
                    "Autonomous training is already in progress; use 'stop' if you want to pause it."
                ),
            )
        stop_event = threading.Event()
        self._continuous_training_stop = stop_event
        self._continuous_training_focus = focus_value
        batch_size = max(5, self._config.web.cycle_batch_size)
        interval = max(0.2, self._config.web.cycle_interval)

        def worker() -> None:
            while not stop_event.is_set():
                report = self.autonomous_train(focus_value, batch_size=batch_size)
                self._memory.record(
                    "autonomy::continuous",
                    report.render(),
                    0.66,
                    "autonomous_web",
                )
                stop_event.wait(interval)

        thread = threading.Thread(
            target=worker,
            name="eidolon-autonomous-training",
            daemon=True,
        )
        thread.start()
        self._continuous_training_thread = thread
        return AutoTrainingStatus(
            running=True,
            focus=focus_value,
            message="Autonomous crawl launched; I'll keep gathering lessons until you say 'stop'.",
        )

    def stop_autonomous_training(self) -> AutoTrainingStatus:
        thread = self._continuous_training_thread
        if not thread or not thread.is_alive():
            return AutoTrainingStatus(
                running=False,
                focus=None,
                message="No autonomous training loop is currently running.",
            )
        assert self._continuous_training_stop is not None
        self._continuous_training_stop.set()
        thread.join(timeout=5)
        focus_value = self._continuous_training_focus
        self._continuous_training_thread = None
        self._continuous_training_stop = None
        self._continuous_training_focus = None
        self._personality.adjust(confidence=0.02, integrity=0.02)
        return AutoTrainingStatus(
            running=False,
            focus=focus_value,
            message="Autonomous crawl halted; summaries are preserved in the memory web.",
        )

    def is_autonomous_training_running(self) -> bool:
        thread = self._continuous_training_thread
        return bool(thread and thread.is_alive())

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
                f"- {domain.title()} → {aspect or 'general focus'}: this lesson shows it {benefit}."
            )
        if not evidence_lines:
            evidence_lines.append("- No matching memories yet; please share more training input when ready.")
        return "\n".join(evidence_lines)

    def _compose_reasoning_block(self, analysis: CortexResult) -> str:
        lines = []
        for response in analysis.responses:
            lines.append(f"- {response.agent.title()}: {response.insight}")
        if analysis.experiments:
            experiment_phrases = [
                f"{result.description} ({'success' if result.success else 'learning opportunity'})"
                for result in analysis.experiments[:3]
            ]
            lines.append(f"- Experiments: {', '.join(experiment_phrases)}")
        else:
            lines.append("- Experiments: none needed; relied on validated precedents.")
        lines.append(f"- Reflection: {analysis.reflection.rationale}")
        lines.append(f"- Synthesis: {analysis.reasoning_summary}")
        return "\n".join(lines)

    def _interpret_intent(
        self, message: str, memories: Iterable[MemoryEntry]
    ) -> str:
        cleaned_tokens = []
        for token in message.split():
            stripped = token.strip(".,!?;:").lower()
            if len(stripped) >= 4 and stripped not in cleaned_tokens:
                cleaned_tokens.append(stripped)
            if len(cleaned_tokens) >= 4:
                break
        memory_list = list(memories)
        if memory_list:
            focus_topic = memory_list[0].topic.replace("::", " → ")
        else:
            focus_topic = "the idea you raised"
        if cleaned_tokens:
            keywords = ", ".join(cleaned_tokens)
            return f"I'm interpreting your request through the lens of {keywords} with focus on {focus_topic}."
        return f"I'm interpreting your request with focus on {focus_topic}."

    def _compose_reply_summary(
        self,
        message: str,
        responses: Iterable[AgentResponse],
        strategic_notes: str,
        reasoning_summary: str,
    ) -> str:
        summary_bits = []
        reasoning_insight = next(
            (response.insight for response in responses if response.agent == "reasoning"),
            None,
        )
        logic_insight = next(
            (response.insight for response in responses if response.agent == "logic"),
            None,
        )
        if reasoning_insight:
            summary_bits.append(reasoning_insight)
        if strategic_notes:
            for piece in strategic_notes.split("|"):
                trimmed = piece.strip()
                if trimmed:
                    summary_bits.append(trimmed)
        if not summary_bits:
            summary_bits.append(reasoning_summary)
        if logic_insight:
            summary_bits.append(logic_insight)
        deduped = []
        for bit in summary_bits:
            if bit and bit not in deduped:
                deduped.append(bit)
        final_summary = " ".join(deduped)
        if not final_summary.endswith("."):
            final_summary += "."
        return final_summary

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
        if not self._autonomous_bootstrap_complete:
            report = self.autonomous_train()
            if report.imported:
                self._memory.record(
                    "autonomy::startup",
                    "Initial autonomous training cycle completed.",
                    0.68,
                    "system",
                )
            self._autonomous_bootstrap_complete = True
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
