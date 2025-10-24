"""Kernel orchestrates engine components."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, Any, Iterable, Optional, List

from .config import EidolonConfig
from .state import PersonalityState
from .cortex import Cortex, CortexResult, AgentResponse
from .memory import MemoryWeb, MemoryEntry
from .forge import Forge
from .firewall import FirewallRing
from .reflection import ReflectionEngine
from .training import TrainingGround, TrainingRecord
from .web_growth import WebGrowthSystem, WebFinding, AutoTrainingReport, AutoTrainingHighlight
from .conversation import ConversationDatastore, ConversationPattern
from .language import LanguageEngine, SemanticFrame
from .speech import SpeechAcademy
from .dataset import load_seed_training_corpus
from .curriculum import load_foundational_datastores


@dataclass
class ChatResult:
    """Response object returned by conversational turns."""

    prompt: str
    reply: str
    analysis: CortexResult

    def render(self) -> str:
        lines = [
            "Eidolon Prime — Conversation Output",
            "===============================",
            "🗣️ Reply:",
            self.reply,
            "",
            "🧠 Reasoning Trail:",
            self.analysis.render(),
        ]
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
        conversation: ConversationDatastore,
        language: LanguageEngine,
        speech: SpeechAcademy,
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
        self._conversation = conversation
        self._language = language
        self._speech = speech
        self._autonomy_initialized = False
        self._seed_initialized = False
        self._autonomous_bootstrap_complete = False
        self._continuous_training_thread: Optional[threading.Thread] = None
        self._continuous_training_stop: Optional[threading.Event] = None
        self._continuous_training_focus: Optional[str] = None
        self._background_warmup_thread: Optional[threading.Thread] = None

    def process_request(self, prompt: str) -> CortexResult:
        return self._cortex.process(prompt)

    def status(self) -> KernelStatus:
        resources = {
            "compute_budget": self._config.resources.compute_budget,
            "max_parallel_agents": self._config.resources.max_parallel_agents,
            "experiment_limit": self._config.resources.experiment_limit,
            "response_delay": self._config.resources.response_delay,
        }
        return KernelStatus(resources, self._personality.describe(), self._memory.summarize())

    def permits_command(self, command: str) -> bool:
        return self._firewall.permits(command)

    def train(self, payload: str) -> TrainingRecord:
        self._firewall.inspect("train", payload)
        record = self._training.ingest(payload)
        self._personality.adjust(confidence=0.01, curiosity=0.02)
        lowered_topic = record.topic.lower()
        if any(keyword in lowered_topic for keyword in ("conversation", "dialog", "tone")):
            self._conversation.ingest_highlights(
                ((record.topic, record.content, record.content),)
            )
        return record

    def chat(self, message: str) -> ChatResult:
        self._firewall.inspect("talk", message)
        self._speech.observe_message(message, self._memory)
        analysis = self._cortex.process(message)
        refresh_report: AutoTrainingReport | None = None
        if self._should_refresh_context(message, analysis):
            refresh_report = self.autonomous_train(message, batch_size=6)
            self._memory.record(
                "websearch::chat",
                refresh_report.render(),
                0.66,
                "autonomous_web",
            )
            analysis = self._cortex.process(message)
            analysis.reasoning_summary = (
                analysis.reasoning_summary
                + f" I refreshed context with a web-assisted practice batch (stage {refresh_report.curriculum_stage}, quiz {refresh_report.quiz_score:.2f})."
            )
        intent, affect = self._infer_intent_and_affect(message)
        pattern = self._conversation.select_pattern(intent, affect)
        frame = self._build_semantic_frame(message, intent, affect, analysis, pattern)
        reply_body, lexical = self._language.compose_reply(
            frame,
            pattern.structure,
            pattern.register,
            self._personality.describe(),
        )
        tone_header = self._describe_tone(pattern.tone)
        reply = f"{tone_header}\n\n{reply_body}"
        response_delay = max(0.0, min(2.0, self._config.resources.response_delay))
        if response_delay:
            time.sleep(response_delay)
        success_score = self._estimate_success(analysis, lexical, len(frame.evidence))
        self._conversation.register_turn(
            pattern.pattern_id,
            intent=intent,
            user_affect=affect,
            tone=pattern.tone,
            structure=pattern.structure,
            lexical_variety=lexical,
            success=success_score,
            reasoning_trace=analysis.reasoning_summary,
        )
        if success_score > 0.7:
            self._personality.adjust(empathy=0.02, confidence=0.01)
        else:
            self._personality.adjust(empathy=0.005)
        self._memory.record("conversation", f"user::{message}", 0.6, "collaboration")
        self._memory.record("conversation", f"eidolon::{reply}", 0.68, "collaboration")
        self._memory.record(
            "conversation::output_area",
            f"Reply displayed in output area for '{message}'",
            0.7,
            "collaboration",
        )
        if refresh_report:
            self._memory.record(
                "conversation::refresh",
                f"Triggered web/practice batch for '{message}': {refresh_report.render()}",
                0.64,
                "autonomous_web",
            )
        return ChatResult(message, reply, analysis)

    def autonomous_train(
        self, focus: str | None = None, *, batch_size: Optional[int] = None
    ) -> AutoTrainingReport:
        """Trigger a curated crawl across trusted external sources."""

        focus_text = (focus or "").strip()
        actual_batch = batch_size or self._config.web.cycle_batch_size
        report = self._web_growth.autonomous_training(focus_text or None, batch_size=actual_batch)
        practice = self._speech.run_batch(
            focus=focus_text,
            batch_size=max(6, min(14, actual_batch + 4)),
            conversation=self._conversation,
            language=self._language,
            personality_snapshot=self._personality.describe(),
            memory=self._memory,
        )
        if practice:
            self._memory.record(
                f"speech_practice::summary::{practice.phase}",
                practice.highlight_summary(),
                0.68 + 0.2 * practice.average_success,
                "speech_practice",
            )
            highlight = AutoTrainingHighlight(
                source=f"speechlab://{practice.phase}",
                topic=f"Speech practice — {practice.phase}",
                summary=practice.highlight_summary(),
                insight=practice.highlight_insight(),
                tier="S",
                kind="practice",
            )
            report.highlights.append(highlight)
            report.imported += len(practice.outcomes)
            if practice.phase_complete:
                self._personality.adjust(confidence=0.02, empathy=0.02)
        if report.imported:
            self._personality.adjust(curiosity=0.04, confidence=0.02)
        else:
            self._personality.adjust(curiosity=0.01)
        summary_text = report.render()
        self._memory.record("autonomy::report", summary_text, 0.6, "autonomous_web")
        self._conversation.ingest_highlights(
            (
                highlight.topic,
                highlight.summary,
                highlight.insight,
            )
            for highlight in report.highlights
        )
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

    def _should_refresh_context(self, message: str, analysis: CortexResult) -> bool:
        if len(message.split()) < 3:
            return False
        if len(analysis.related_memories) >= 3:
            return False
        keywords = {token for token in message.lower().split() if len(token) > 3}
        if not keywords:
            return False
        return True

    def _infer_intent_and_affect(self, message: str) -> tuple[str, str]:
        lowered = message.lower().strip()
        intent = "explain"
        greeting_prefixes = ("hello", "hi", "hey", "greetings", "good morning", "good evening", "good afternoon")
        if any(lowered.startswith(prefix) for prefix in greeting_prefixes):
            intent = "conversation"
        if "?" in message or any(
            lowered.startswith(prefix)
            for prefix in ("how", "what", "why", "where", "when")
        ):
            intent = "question"
        elif any(keyword in lowered for keyword in ("plan", "design", "build", "fix")):
            intent = "problem_solving"
        elif any(keyword in lowered for keyword in ("motivate", "inspire", "story")):
            intent = "motivate"
        affect = self._compute_user_affect(lowered)
        return intent, affect

    def _compute_user_affect(self, lowered: str) -> str:
        negative_markers = {"stuck", "confused", "worried", "frustrated", "angry"}
        positive_markers = {"excited", "happy", "thanks", "love", "great"}
        if any(marker in lowered for marker in negative_markers):
            return "stressed"
        if any(marker in lowered for marker in positive_markers):
            return "positive"
        return "neutral"

    def _build_semantic_frame(
        self,
        message: str,
        intent: str,
        affect: str,
        analysis: CortexResult,
        pattern: ConversationPattern,
    ) -> SemanticFrame:
        topic = self._derive_topic(message, analysis.related_memories)
        key_points = self._extract_key_points(analysis.responses, analysis.reasoning_summary)
        evidence = self._extract_evidence(analysis.related_memories)
        actions = self._extract_actions(analysis)
        emotional_tone = self._derive_emotional_tone(pattern.tone, affect)
        call_to_action = self._craft_call_to_action(analysis, actions)
        outcome = analysis.reflection.rationale
        return SemanticFrame(
            intent=intent,
            topic=topic,
            user_message=message,
            key_points=key_points,
            evidence=evidence,
            actions=actions,
            emotional_tone=emotional_tone,
            call_to_action=call_to_action,
            outcome=outcome,
        )

    def _derive_topic(self, message: str, memories: Iterable[MemoryEntry]) -> str:
        memory_list = list(memories)
        if memory_list:
            return memory_list[0].topic.replace("::", " → ")
        tokens = [token.strip(".,!?;:") for token in message.split() if len(token) > 3]
        return " ".join(tokens[:4]) if tokens else message[:32]

    def _extract_key_points(
        self, responses: Iterable[AgentResponse], reasoning_summary: str
    ) -> List[str]:
        insights = []
        for response in responses:
            humanized = self._humanize_insight(response)
            if humanized not in insights:
                insights.append(humanized)
            if len(insights) >= 4:
                break
        if not insights and reasoning_summary:
            insights.append(reasoning_summary)
        return insights

    def _extract_actions(self, analysis: CortexResult) -> List[str]:
        actions: List[str] = []
        for result in analysis.experiments:
            if result.success:
                summary = self._summarize_experiment(result.description)
                actions.append(
                    f"pilot an experiment to {summary} so we validate the approach"
                )
        if analysis.reasoning_summary and analysis.reasoning_summary not in actions:
            actions.append(analysis.reasoning_summary)
        return actions[:4]

    def _humanize_insight(self, response: AgentResponse) -> str:
        text = response.insight.strip()
        if response.agent == "logic" and text.startswith("Mapped your request to"):
            return text.replace("Mapped your request to", "Your request aligns with", 1)
        if response.agent == "logic" and text.startswith("Structured the prompt"):
            return text.replace("Structured the prompt", "I structured the prompt", 1)
        if response.agent == "curiosity" and text.startswith("Propose"):
            return text.replace("Propose", "I propose", 1)
        if response.agent == "ethics" and text.startswith("Checked prompt"):
            return text.replace("Checked prompt", "Ethics review confirms", 1)
        if response.agent == "reasoning" and text.startswith("Synthesized"):
            return text.replace("Synthesized", "I synthesized", 1)
        return text

    def _summarize_experiment(self, description: str) -> str:
        text = description.strip()
        text = text.replace("experiment", "")
        if text.startswith("Mapped your request to"):
            return text.replace("Mapped your request to", "confirm the request aligns with", 1).rstrip(".")
        if text.startswith("I structured the prompt"):
            return text.replace("I structured the prompt", "stress-test the prompt", 1).rstrip(".")
        return text.rstrip(".")

    def _extract_evidence(self, memories: Iterable[MemoryEntry]) -> List[str]:
        evidence_lines: List[str] = []
        for entry in list(memories)[:4]:
            snippet = entry.content
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            evidence_lines.append(
                f"{entry.topic} → {snippet} (confidence {entry.confidence:.2f})"
            )
        return evidence_lines

    def _derive_emotional_tone(self, desired_tone: str, affect: str) -> str:
        if affect == "stressed":
            return "calm and steady"
        if self._personality.empathy > 0.7:
            return "deeply supportive"
        if desired_tone == "encouraging" and self._personality.curiosity > 0.6:
            return "encouraging and exploratory"
        if desired_tone == "steady" and self._personality.confidence > 0.6:
            return "confident and pragmatic"
        return desired_tone or "balanced"

    def _craft_call_to_action(
        self, analysis: CortexResult, actions: List[str]
    ) -> str:
        if actions:
            return f"Let's act on {actions[0]} next."
        return (
            analysis.reasoning_summary
            or "I'm ready to dig further once you highlight the next angle."
        )

    def _estimate_success(
        self, analysis: CortexResult, lexical: float, evidence_count: int
    ) -> float:
        base = 0.55 + 0.25 * min(1.0, lexical)
        if analysis.reflection.accepted:
            base += 0.08
        base += min(0.08, evidence_count * 0.02)
        if analysis.experiments:
            successful = sum(1 for result in analysis.experiments if result.success)
            base += min(0.07, successful * 0.02)
        return max(0.0, min(1.0, base))

    def enforce_security(self, command: str, payload: str) -> None:
        self._firewall.inspect(command, payload)

    def bootstrap(self) -> None:
        """Auto-ingest trusted web knowledge once per engine lifetime."""

        if self._autonomy_initialized:
            return

        if not self._seed_initialized:
            seeded = load_seed_training_corpus(self._memory)
            foundations = load_foundational_datastores(self._memory)
            if seeded:
                self._personality.adjust(confidence=0.08, curiosity=0.05, integrity=0.03)
            if foundations:
                total = sum(foundations.values())
                self._personality.adjust(confidence=0.04, empathy=0.03)
                self._memory.record(
                    "curriculum::foundation",
                    f"Loaded foundational datasets: {foundations} (total {total}).",
                    0.82,
                    "system",
                )
            practice = self._speech.run_batch(
                focus="foundational conversation",
                batch_size=8,
                conversation=self._conversation,
                language=self._language,
                personality_snapshot=self._personality.describe(),
                memory=self._memory,
            )
            if practice:
                self._memory.record(
                    "speech_practice::bootstrap",
                    practice.highlight_summary(),
                    0.7 + 0.2 * practice.average_success,
                    "speech_practice",
                )
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
        if self._background_warmup_thread is None:
            self._start_background_warmup()
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

    def _start_background_warmup(self) -> None:
        """Launch a short warmup loop that keeps the academy active."""

        def worker() -> None:
            for focus in ("warmup vocabulary", "warmup reasoning", "warmup dialogue"):
                report = self.autonomous_train(focus, batch_size=12)
                self._memory.record(
                    "autonomy::warmup",
                    f"Warmup batch for {focus}: {report.render()}",
                    0.64,
                    "autonomous_web",
                )
                time.sleep(0.2)

        thread = threading.Thread(target=worker, name="eidolon-warmup", daemon=True)
        thread.start()
        self._background_warmup_thread = thread

    def _describe_tone(self, preferred: Optional[str] = None) -> str:
        if preferred == "encouraging" and self._personality.empathy > 0.5:
            return "I'll keep an encouraging tone while we explore this together."
        if preferred == "steady":
            return "I'll stay steady and pragmatic so we can tackle the moving parts."
        if preferred == "curious":
            return "I'll approach this with inquisitive energy to surface new angles."
        if self._personality.empathy > 0.7:
            return "I'm feeling especially supportive."
        if self._personality.curiosity > 0.6:
            return "Curiosity is high, so let's explore together."
        if self._personality.confidence < 0.4:
            return "I'll take a careful approach."
        return "Here's my considered response."
