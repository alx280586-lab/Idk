"""Kernel orchestrates engine components."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, Any, Iterable, Optional, List, Tuple

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
from .comprehension import MessageComprehender, MessageUnderstanding
from .synthetic import SyntheticThoughtEngine, SyntheticThoughtPlan
from .orchestrator import OrchestratorResult
from .reasoning import ReasoningProfile
from .knowledge import KnowledgeGapMonitor
from .neural import (
    UltraNeuralNetwork,
    NeuralActivation,
    NarrowCollective,
    CollectiveReport,
)
from .distillation import DistillationCoach


_SMALLTALK_VOCAB = {
    "hi",
    "hello",
    "hey",
    "heya",
    "hiya",
    "how",
    "are",
    "you",
    "doing",
    "today",
    "tonight",
    "this",
    "morning",
    "afternoon",
    "evening",
    "hope",
    "your",
    "day",
    "going",
    "well",
    "good",
    "great",
    "nice",
    "to",
    "meet",
    "pleased",
    "thanks",
    "thank",
    "friend",
    "there",
    "what's",
    "whats",
    "up",
    "greetings",
    "hello!",
    "yo",
    "sup",
    "greet",
}


@dataclass
class ChatResult:
    """Response object returned by conversational turns."""

    prompt: str
    reply: str
    speech: str
    analysis: CortexResult
    plan: Optional[SyntheticThoughtPlan] = None
    activation: Optional[NeuralActivation] = None
    collective: Optional[CollectiveReport] = None

    def render(self) -> str:
        lines = [
            "Eidolon Prime — Conversation Output",
            "===============================",
            "💬 Final Reply:",
            self.reply,
            "",
            "🔊 Speech Output:",
            self.speech,
            "",
            "🧠 Reasoning Trail:",
            self.analysis.render(),
        ]
        if self.plan:
            lines.extend(["", "🧩 Synthetic Thought Plan:", self.plan.render()])
        if self.activation:
            lines.extend(
                [
                    "",
                    "🕸️ Neural Activation:",
                    self.activation.summary,
                ]
            )
        if self.collective:
            lines.extend(
                [
                    "",
                    "🤝 Specialist Collective:",
                    self.collective.consensus,
                ]
            )
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


@dataclass
class DistillationReceipt:
    """Summary of a conversational distillation cycle."""

    topic: Optional[str]
    stored: int

    def render(self) -> str:
        topic_text = self.topic or "general dialogue foundations"
        if self.stored == 0:
            return f"No new distillation entries were added for {topic_text}."
        return (
            f"Distillation captured {self.stored} dialogue exemplars for {topic_text}.\n"
            "They are now available to influence future conversations."
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
        comprehension: MessageComprehender,
        synthetic: SyntheticThoughtEngine,
        reasoning: ReasoningProfile,
        knowledge: KnowledgeGapMonitor,
        neural: UltraNeuralNetwork,
        collective: NarrowCollective,
        distillation: DistillationCoach,
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
        self._comprehension = comprehension
        self._synthetic = synthetic
        self._reasoning = reasoning
        self._knowledge = knowledge
        self._neural = neural
        self._collective = collective
        self._distillation = distillation
        self._autonomy_initialized = False
        self._seed_initialized = False
        self._autonomous_bootstrap_complete = False
        self._continuous_training_thread: Optional[threading.Thread] = None
        self._continuous_training_stop: Optional[threading.Event] = None
        self._continuous_training_focus: Optional[str] = None
        self._background_warmup_thread: Optional[threading.Thread] = None
        self._distilled_topics: set[str] = set()

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
        self._maybe_distill(record.topic)
        self._synthetic.observe_training_report(
            f"manual-train::{record.topic}::{record.content}"
        )
        return record

    def distill(self, topic: Optional[str] = None) -> DistillationReceipt:
        captured = self._distillation.run(topic)
        if topic:
            self._distilled_topics.add(topic.lower())
        return DistillationReceipt(topic, captured)

    def chat(self, message: str) -> ChatResult:
        self._firewall.inspect("talk", message)
        understanding = self._comprehension.analyse(message)
        is_smalltalk = self._is_smalltalk_message(understanding)
        self._maybe_distill(understanding.focus_text() or understanding.topic_hint())
        gap_report = self._knowledge.evaluate(understanding, self._memory)
        understanding.unknown_terms = gap_report.unresolved_terms()
        understanding.researched_terms = gap_report.resolved_terms()
        understanding.coding_terms = list(dict.fromkeys(gap_report.coding_terms))
        gap_resolution_notes: List[str] = []
        unresolved_gaps = gap_report.unresolved()
        max_gap_checks = min(3, len(unresolved_gaps))
        for gap in unresolved_gaps[:max_gap_checks]:
            if is_smalltalk:
                break
            gap_report.triggered_queries.append(gap.term)
            report = self.autonomous_train(gap.term, batch_size=6)
            resolved_gap = self._knowledge.register_resolution(gap, report, self._memory)
            if resolved_gap.resolved:
                understanding.researched_terms.append(resolved_gap.term)
                self._reasoning.register_gap_resolution(
                    resolved_gap.term, resolved_gap.sources
                )
                gap_resolution_notes.append(resolved_gap.summary)
        understanding.unknown_terms = gap_report.unresolved_terms()
        understanding.researched_terms = list(
            dict.fromkeys(gap_report.resolved_terms())
        )
        self._speech.observe_message(message, self._memory)
        plan = self._synthetic.plan(message, understanding, self._memory)
        analysis = self._cortex.process(
            message,
            understanding=understanding,
            plan=plan,
            gap_report=gap_report,
        )
        if analysis.reasoning_summary is None:
            analysis.reasoning_summary = ""
        if is_smalltalk:
            analysis.reasoning_summary = (
                "Recognised a friendly greeting, prioritised rapport, and invited a follow-up question."
            )
        activation = self._neural.activate(
            message,
            understanding,
            plan,
            analysis.orchestration,
        )
        if activation.summary not in analysis.reasoning_summary and not is_smalltalk:
            if analysis.reasoning_summary:
                analysis.reasoning_summary += "\n\n" + activation.summary
            else:
                analysis.reasoning_summary = activation.summary
        refresh_report: AutoTrainingReport | None = None
        if self._should_refresh_context(message, analysis, understanding) and not is_smalltalk:
            focus_query = understanding.focus_text() or message
            refresh_report = self.autonomous_train(focus_query, batch_size=6)
            self._memory.record(
                "websearch::chat",
                refresh_report.render(),
                0.66,
                "autonomous_web",
            )
            plan = self._synthetic.plan(message, understanding, self._memory)
            analysis = self._cortex.process(
                message,
                understanding=understanding,
                plan=plan,
                gap_report=gap_report,
            )
            activation = self._neural.activate(
                message,
                understanding,
                plan,
                analysis.orchestration,
            )
            analysis.reasoning_summary = (
                analysis.reasoning_summary
                + f" I refreshed context with a web-assisted practice batch (stage {refresh_report.curriculum_stage}, quiz {refresh_report.quiz_score:.2f})."
            )
        harvested_reports: List[AutoTrainingReport] = []
        if not is_smalltalk:
            processed_queries = set()
            for query in plan.harvest_queries[
                : self._config.synthetic.max_harvest_queries
            ]:
                normalized = query.lower()
                if normalized in processed_queries:
                    continue
                processed_queries.add(normalized)
                report = self.autonomous_train(query, batch_size=8)
                harvested_reports.append(report)
            if harvested_reports:
                plan = self._synthetic.plan(message, understanding, self._memory)
                analysis = self._cortex.process(
                    message,
                    understanding=understanding,
                    plan=plan,
                    gap_report=gap_report,
                )
                activation = self._neural.activate(
                    message,
                    understanding,
                    plan,
                    analysis.orchestration,
                )
        if gap_report.resolved_terms() and not is_smalltalk:
            reinforcement = ", ".join(gap_report.resolved_terms()[:4])
            addition = (
                "Vocabulary reinforcement completed: "
                + reinforcement
                + "."
            )
            if analysis.reasoning_summary:
                analysis.reasoning_summary += "\n\n" + addition
            else:
                analysis.reasoning_summary = addition
        if gap_resolution_notes and not is_smalltalk:
            combined = " | ".join(gap_resolution_notes[:3])
            self._memory.record(
                "conversation::gap_resolution",
                combined,
                0.68,
                "knowledge_gap",
            )
            analysis.reasoning_summary += (
                f" Synthetic plan harvested {len(harvested_reports)} extra knowledge batches."
            )
        intent, affect = self._infer_intent_and_affect(message, understanding)
        pattern = self._conversation.select_pattern(intent, affect)
        if intent == "current_events":
            briefing_pattern = self._conversation.get_pattern("news.world.briefing")
            if briefing_pattern is not None:
                pattern = briefing_pattern
        if (
            understanding.coding_terms
            and pattern.structure != "diagnose→code→next-step"
            and pattern.intent not in {"essay", "creative", "current_events"}
        ):
            for candidate in self._conversation.all_patterns():
                if candidate.pattern_id == "code.review.sequence":
                    pattern = candidate
                    break
        if is_smalltalk:
            smalltalk_pattern = self._conversation.get_pattern("dialogue.loop.reflect")
            if smalltalk_pattern:
                pattern = smalltalk_pattern
        self._conversation.ingest_highlights(
            (
                f"conversation::focus::{index}",
                highlight,
                highlight,
            )
            for index, highlight in enumerate(understanding.highlights(), start=1)
        )
        collective = self._collective.consensus(
            message,
            activation,
            understanding,
            plan,
        )
        if collective:
            addition = (
                collective.consensus
                + " Specialist confidence "
                + f"{collective.confidence:.2f}."
            )
            if addition not in analysis.reasoning_summary:
                if analysis.reasoning_summary:
                    analysis.reasoning_summary += "\n\n" + addition
                else:
                    analysis.reasoning_summary = addition
        frame = self._build_semantic_frame(
            message,
            intent,
            affect,
            analysis,
            pattern,
            understanding,
            plan,
            analysis.orchestration,
            activation,
            collective,
            smalltalk=is_smalltalk,
        )
        if understanding.coding_terms and pattern.register not in {
            "essay_formal",
            "creative_narrative",
            "current_affairs",
        }:
            preferred_register = "engineering"
        else:
            preferred_register = pattern.register
        if is_smalltalk:
            reply_body, lexical = self._compose_smalltalk_reply(understanding)
        else:
            reply_body, lexical = self._language.compose_reply(
                frame,
                pattern.structure,
                preferred_register,
                self._personality.describe(),
            )
        paragraph_limit = self._determine_paragraph_limit(pattern, understanding)
        reply_body = self._limit_paragraphs(reply_body, paragraph_limit)
        if is_smalltalk:
            tone_header = "Hi there! I'm glad you reached out."
        else:
            tone_header = self._describe_tone(pattern.tone)
        reply = f"{tone_header}\n\n{reply_body}"
        speech_output = self._speech.vocalize(reply_body)
        response_delay = max(0.0, min(2.0, self._config.resources.response_delay))
        if response_delay:
            time.sleep(response_delay)
        success_score = self._estimate_success(
            analysis, lexical, len(frame.evidence), plan
        )
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
            "conversation::speech", speech_output, 0.67, "speech_output"
        )
        self._memory.record(
            "conversation::understanding",
            understanding.summary(),
            0.64,
            "conversation",
        )
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
        for report in harvested_reports:
            self._memory.record(
                "conversation::synthetic_harvest",
                report.render(),
                0.63,
                "autonomous_web",
            )
        self._memory.record(
            "conversation::synthetic_plan",
            plan.render(),
            0.69,
            "synthetic_plan",
        )
        return ChatResult(
            message,
            reply,
            speech_output,
            analysis,
            plan,
            activation,
            collective,
        )

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
        self._reasoning.observe_training(report)
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
        self._synthetic.observe_training_report(summary_text)
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

    def _should_refresh_context(
        self,
        message: str,
        analysis: CortexResult,
        understanding: MessageUnderstanding | None = None,
    ) -> bool:
        if understanding and understanding.question and len(analysis.related_memories) < 4:
            return True
        if len(analysis.related_memories) >= 3:
            return False
        if understanding and len(understanding.focus_terms) >= 3:
            return True
        if understanding and understanding.urgency:
            return True
        if len(message.split()) < 3:
            return False
        keywords = {token for token in message.lower().split() if len(token) > 3}
        return bool(keywords)

    def _infer_intent_and_affect(
        self, message: str, understanding: MessageUnderstanding
    ) -> tuple[str, str]:
        lowered = message.lower().strip()
        intent = "explain"
        greeting_prefixes = ("hello", "hi", "hey", "greetings", "good morning", "good evening", "good afternoon")
        if any(lowered.startswith(prefix) for prefix in greeting_prefixes):
            intent = "conversation"
        essay_request = any(
            phrase in lowered
            for phrase in (
                "write an essay",
                "write a multi-paragraph essay",
                "multi paragraph essay",
                "compose an essay",
                "thesis statement",
            )
        ) or "essay" in understanding.focus_terms
        creative_request = any(
            phrase in lowered
            for phrase in (
                "creative writing",
                "write a story",
                "craft a narrative",
                "imaginative scene",
            )
        )
        world_request = any(
            phrase in lowered
            for phrase in (
                "world today",
                "current events",
                "news update",
                "what is happening",
            )
        )
        if essay_request:
            intent = "essay"
        elif creative_request:
            intent = "creative"
        elif world_request:
            intent = "current_events"
        if understanding.question:
            if intent not in {"essay", "creative", "current_events"}:
                intent = "question"
        elif intent not in {"essay", "creative", "current_events"}:
            if any(keyword in lowered for keyword in ("plan", "design", "build", "fix")):
                intent = "problem_solving"
            elif any(keyword in lowered for keyword in ("motivate", "inspire", "story")):
                if not creative_request:
                    intent = "motivate"
            elif understanding.command_clauses:
                intent = "problem_solving"
        if understanding.coding_terms and intent not in {"essay", "creative", "current_events"}:
            intent = "problem_solving"
        affect = understanding.affect or self._compute_user_affect(lowered)
        if understanding.urgency and affect == "neutral":
            affect = "stressed"
        return intent, affect

    def _compute_user_affect(self, lowered: str) -> str:
        negative_markers = {"stuck", "confused", "worried", "frustrated", "angry"}
        positive_markers = {"excited", "happy", "thanks", "love", "great"}
        if any(marker in lowered for marker in negative_markers):
            return "stressed"
        if any(marker in lowered for marker in positive_markers):
            return "positive"
        return "neutral"

    def _is_smalltalk_message(self, understanding: MessageUnderstanding) -> bool:
        tokens = [token for token in understanding.tokens if token]
        if not tokens:
            return False
        unique_tokens = set(tokens)
        greeting_core = unique_tokens - {"i", "im", "i'm", "it's", "its", "am"}
        if greeting_core and greeting_core.issubset(_SMALLTALK_VOCAB):
            return True
        if tokens[0] in {"hi", "hello", "hey", "yo"}:
            unfamiliar = unique_tokens - (
                _SMALLTALK_VOCAB | {"i", "im", "i'm", "it's", "its", "am"}
            )
            if len(unfamiliar) <= 1:
                return True
        if len(tokens) <= 6 and unique_tokens.issubset(
            _SMALLTALK_VOCAB | {"i", "im", "i'm", "it's", "its", "am"}
        ):
            return True
        return False

    def _compose_smalltalk_reply(
        self, understanding: MessageUnderstanding
    ) -> Tuple[str, float]:
        greeting_sentence = (
            understanding.sentences[0]
            if understanding.sentences
            else understanding.original.strip()
        )
        acknowledgement = "Thanks for checking in."
        if greeting_sentence:
            acknowledgement = f"Thanks for the greeting — I heard \"{greeting_sentence}\"."
        follow_up = "I'm doing well and ready to help with anything you're curious about."
        invitation = "Whenever you're ready, let me know what you'd like to explore next."
        reply_text = f"{acknowledgement} {follow_up} {invitation}"
        unique_count = len({token for token in understanding.tokens if len(token) > 2})
        lexical = min(0.9, 0.45 + 0.05 * unique_count)
        return reply_text, lexical

    def _maybe_distill(self, topic_hint: Optional[str]) -> None:
        if not topic_hint:
            return
        lowered = topic_hint.lower().strip()
        if not lowered or lowered in self._distilled_topics:
            return
        captured = self._distillation.run(lowered, limit=4)
        if captured:
            self._distilled_topics.add(lowered)

    def _build_semantic_frame(
        self,
        message: str,
        intent: str,
        affect: str,
        analysis: CortexResult,
        pattern: ConversationPattern,
        understanding: MessageUnderstanding,
        plan: Optional[SyntheticThoughtPlan],
        orchestration: Optional[OrchestratorResult],
        activation: NeuralActivation,
        collective: Optional[CollectiveReport],
        *,
        smalltalk: bool = False,
    ) -> SemanticFrame:
        if smalltalk:
            topic = understanding.topic_hint() or "your greeting"
            greeting_sentence = (
                understanding.sentences[0]
                if understanding.sentences
                else understanding.original.strip()
            )
            key_points: List[str] = []
            if greeting_sentence:
                key_points.append(
                    f"Recognised the greeting '{greeting_sentence}' and mirrored the tone."
                )
            evidence: List[str] = []
            actions = [
                "Invite the user to share any questions or tasks they want to tackle next."
            ]
            emotional_tone = "warm"
            call_to_action = "Tell me what you'd like to talk about or build."
            outcome = "Greeting acknowledged and invitation issued."
            return SemanticFrame(
                intent="conversation",
                topic=topic,
                user_message=understanding.original,
                key_points=key_points,
                evidence=evidence,
                actions=actions,
                emotional_tone=emotional_tone,
                call_to_action=call_to_action,
                outcome=outcome,
            )
        topic = self._derive_topic(
            message, analysis.related_memories, understanding, plan
        )
        key_points = self._extract_key_points(
            analysis.responses,
            analysis.reasoning_summary,
            understanding,
            plan,
            orchestration,
        )
        if activation.attention_terms:
            key_points.extend(
                f"Neural focus: {term}" for term in activation.attention_terms[:4]
            )
        if collective:
            key_points.append(collective.consensus)
        evidence = self._extract_evidence(
            analysis.related_memories,
            understanding,
            plan,
            orchestration,
        )
        if collective:
            evidence.extend(
                insight.contribution for insight in collective.insights[:3]
            )
        actions = self._extract_actions(
            analysis,
            understanding,
            plan,
            orchestration,
        )
        if collective and collective.adjustments:
            adjustment_text = ", ".join(
                f"{key.replace('_', ' ')}→{value:.2f}"
                for key, value in collective.adjustments.items()
            )
            actions.append(
                f"Collective adjustments applied: {adjustment_text}."
            )
        emotional_tone = self._derive_emotional_tone(pattern.tone, affect, understanding)
        call_to_action = self._craft_call_to_action(analysis, actions, understanding)
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

    def _limit_paragraphs(self, reply_body: str, limit: int) -> str:
        paragraphs = [segment.strip() for segment in reply_body.split("\n\n") if segment.strip()]
        if limit <= 0:
            return "".join(paragraphs)
        if len(paragraphs) <= limit:
            return "\n\n".join(paragraphs)
        preserved = paragraphs[: limit - 1]
        remainder = "\n\n".join(paragraphs[limit - 1 :])
        preserved.append(remainder)
        return "\n\n".join(preserved)

    def _determine_paragraph_limit(
        self, pattern: ConversationPattern, understanding: MessageUnderstanding
    ) -> int:
        structure = pattern.structure
        if "thesis" in structure:
            return 6
        if "hook" in structure and "resolution" in structure:
            return 5
        if "situation" in structure:
            return 4
        if {"script", "roblox"}.issubset(set(understanding.focus_terms)):
            return 4
        if understanding.question and len(understanding.sentences) > 2:
            return 3
        return 2

    def _derive_topic(
        self,
        message: str,
        memories: Iterable[MemoryEntry],
        understanding: MessageUnderstanding,
        plan: Optional[SyntheticThoughtPlan],
    ) -> str:
        memory_list = list(memories)
        if memory_list:
            topic_text = memory_list[0].topic.replace("::", " → ").replace("_", " ")
            parts = [segment.strip() for segment in topic_text.split(" → ") if segment.strip()]
            if parts:
                topic_text = " → ".join(parts[:3])
            return topic_text
        if plan:
            if plan.focus_pairs:
                return plan.focus_pairs[0]
            if plan.focus_terms:
                return " ".join(plan.focus_terms[:4])
        if understanding.focus_pairs:
            return understanding.focus_pairs[0]
        if understanding.focus_terms:
            return " ".join(understanding.focus_terms[:4])
        bias_snapshot = self._reasoning.bias_snapshot(1)
        if bias_snapshot:
            return bias_snapshot[0][0].replace("_", " ")
        tokens = [token.strip(".,!?;:") for token in message.split() if len(token) > 3]
        return " ".join(tokens[:4]) if tokens else message[:32]

    def _extract_key_points(
        self,
        responses: Iterable[AgentResponse],
        reasoning_summary: str,
        understanding: MessageUnderstanding,
        plan: Optional[SyntheticThoughtPlan],
        orchestration: Optional[OrchestratorResult],
    ) -> List[str]:
        insights = []
        for highlight in understanding.highlights():
            if highlight not in insights:
                insights.append(highlight)
        for response in responses:
            humanized = self._humanize_insight(response)
            if humanized not in insights:
                insights.append(humanized)
            if len(insights) >= 4:
                break
        if plan:
            for outline in plan.outline[:3]:
                if outline not in insights:
                    insights.append(outline)
                    if len(insights) >= 6:
                        break
        if orchestration and orchestration.final_text:
            summary_line = orchestration.final_text.split("\n")[0]
            if summary_line and summary_line not in insights:
                insights.append(summary_line)
        if not insights and reasoning_summary:
            insights.append(reasoning_summary)
        return insights

    def _extract_actions(
        self,
        analysis: CortexResult,
        understanding: MessageUnderstanding,
        plan: Optional[SyntheticThoughtPlan],
        orchestration: Optional[OrchestratorResult],
    ) -> List[str]:
        actions: List[str] = []
        for result in analysis.experiments:
            if result.success:
                summary = self._summarize_experiment(result.description)
                actions.append(
                    f"pilot an experiment to {summary} so we validate the approach"
                )
        if analysis.reasoning_summary and analysis.reasoning_summary not in actions:
            actions.append(analysis.reasoning_summary)
        for clause in understanding.command_clauses:
            clean_clause = clause.strip().rstrip(".")
            if clean_clause and clean_clause not in actions:
                actions.append(f"address your request to {clean_clause}")
        if plan and plan.harvest_queries:
            harvest = "; ".join(plan.harvest_queries[:2])
            actions.append(f"research trusted sources via: {harvest}")
        if orchestration and orchestration.evaluation.checklist:
            for item in orchestration.evaluation.checklist:
                actions.append(f"review checklist item: {item}")
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
        if response.agent == "synthetic" and text.startswith("Focus:"):
            return text.replace("Focus:", "Synthetic plan focus:", 1)
        return text

    def _summarize_experiment(self, description: str) -> str:
        text = description.strip()
        text = text.replace("experiment", "")
        if text.startswith("Mapped your request to"):
            return text.replace("Mapped your request to", "confirm the request aligns with", 1).rstrip(".")
        if text.startswith("I structured the prompt"):
            return text.replace("I structured the prompt", "stress-test the prompt", 1).rstrip(".")
        return text.rstrip(".")

    def _extract_evidence(
        self,
        memories: Iterable[MemoryEntry],
        understanding: MessageUnderstanding,
        plan: Optional[SyntheticThoughtPlan],
        orchestration: Optional[OrchestratorResult],
    ) -> List[str]:
        evidence_lines: List[str] = []
        for entry in list(memories)[:4]:
            snippet = entry.content
            if "```" not in snippet and len(snippet) > 160:
                snippet = snippet[:157] + "..."
            evidence_lines.append(
                f"{entry.topic} → {snippet} (confidence {entry.confidence:.2f})"
            )
        if orchestration and orchestration.citations:
            for citation in orchestration.citations[:5]:
                evidence_lines.append(f"Citation: {citation}")
        if understanding.coding_terms and not any("```" in line for line in evidence_lines):
            code_query_terms = understanding.focus_terms[:6] + ["roblox", "blueprint", "code"]
            code_query = " ".join(term for term in code_query_terms if term)
            for candidate in self._memory.search(code_query, limit=6):
                if "```" in candidate.content:
                    evidence_lines.append(
                        f"{candidate.topic} → {candidate.content} (confidence {candidate.confidence:.2f})"
                    )
                    break
        if not evidence_lines and understanding.focus_terms:
            evidence_lines.append(
                "Focus alignment: "
                + ", ".join(understanding.focus_terms[:4])
                + " (derived from your wording)."
            )
        if plan and getattr(plan, "context_links", None):
            for link in plan.context_links[:3]:
                evidence_lines.append(f"Context vault: {link}")
        return evidence_lines

    def _derive_emotional_tone(
        self, desired_tone: str, affect: str, understanding: MessageUnderstanding
    ) -> str:
        if affect == "stressed":
            return "calm and steady"
        if understanding.affect == "positive":
            return "warm and collaborative"
        if self._personality.empathy > 0.7:
            return "deeply supportive"
        if desired_tone == "encouraging" and self._personality.curiosity > 0.6:
            return "encouraging and exploratory"
        if desired_tone == "steady" and self._personality.confidence > 0.6:
            return "confident and pragmatic"
        return desired_tone or "balanced"

    def _craft_call_to_action(
        self,
        analysis: CortexResult,
        actions: List[str],
        understanding: MessageUnderstanding,
    ) -> str:
        if actions:
            return f"Let's act on {actions[0]} next."
        if understanding.command_clauses:
            return f"I'll keep exploring how to {understanding.command_clauses[0]} and report back."
        return (
            analysis.reasoning_summary
            or "I'm ready to dig further once you highlight the next angle."
        )

    def _estimate_success(
        self,
        analysis: CortexResult,
        lexical: float,
        evidence_count: int,
        plan: Optional[SyntheticThoughtPlan] = None,
    ) -> float:
        base = 0.55 + 0.25 * min(1.0, lexical)
        if analysis.reflection.accepted:
            base += 0.08
        base += min(0.08, evidence_count * 0.02)
        if analysis.experiments:
            successful = sum(1 for result in analysis.experiments if result.success)
            base += min(0.07, successful * 0.02)
        if plan and plan.module_traces:
            base += min(0.05, len(plan.module_traces) * 0.01)
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
            synthetic_counts = self._synthetic.seed_memory(self._memory)
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
                self._reasoning.register_foundation(
                    f"Foundational datasets emphasised: {', '.join(sorted(foundations))}"
                )
            if synthetic_counts:
                total_synth = sum(synthetic_counts.values())
                self._memory.record(
                    "synthetic::foundation",
                    f"Seeded synthetic datastores: {synthetic_counts} (total {total_synth}).",
                    0.8,
                    "synthetic_datastore",
                )
                self._reasoning.register_foundation(
                    f"Synthetic datastore seeding: {', '.join(sorted(synthetic_counts))}"
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
            self._knowledge.sync_with_memory(self._memory)
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
        mapping = {
            "encouraging": "Here's an encouraging path forward.",
            "steady": "Let's take this one step at a time.",
            "curious": "Let's explore the question together.",
            "warm": "Here's a warm, thoughtful response.",
            "balanced": "Here's a balanced take that weighs the trade-offs.",
        }
        if preferred and preferred in mapping:
            return mapping[preferred]
        if self._personality.confidence < 0.35:
            return "I'll keep things careful and precise."
        if self._personality.empathy > 0.75:
            return "I'll keep things supportive and clear."
        return "Here's how I'm thinking about it."
