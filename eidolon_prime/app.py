"""Application bootstrap for the Eidolon Prime engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterable

from .config import EidolonConfig, load_config
from .kernel import Kernel
from .cortex import Cortex
from .memory import MemoryWeb
from .forge import Forge
from .firewall import FirewallRing
from .reflection import ReflectionEngine
from .web_growth import WebGrowthSystem
from .collaboration import CollaborationLayer
from .state import PersonalityState
from .training import TrainingGround
from .conversation import ConversationDatastore
from .language import GrammarDatastore, LanguageEngine
from .speech import SpeechAcademy
from .comprehension import MessageComprehender
from .synthetic import SyntheticThoughtEngine
from .reasoning import ReasoningProfile
from .knowledge import KnowledgeGapMonitor
from .planner import DeliberativePlanner
from .retrieval import RetrievalManager
from .knowledge_graph import KnowledgeGraph
from .coherence import CoherenceScorer
from .style import StyleProfile
from .evaluation import EvaluationHarness
from .critics import CriticSuite
from .orchestrator import ReasoningOrchestrator
from .neural import UltraNeuralNetwork, NarrowCollective, NarrowSpecialist
from .ollama import OllamaBridge
from .distillation import DistillationCoach


@dataclass
class EidolonPrimeApp:
    """Convenience wrapper that wires all engine components together."""

    config: EidolonConfig
    kernel: Kernel
    collaboration: CollaborationLayer

    @classmethod
    def from_config_path(cls, path: Optional[str] = None) -> "EidolonPrimeApp":
        config = load_config(path)
        memory = MemoryWeb()
        personality = PersonalityState()
        firewall = FirewallRing(
            config.security.allowed_commands,
            config.security.blocked_phrases,
            config.security.max_payload_length,
        )
        forge = Forge(memory)
        reflection = ReflectionEngine(personality, memory)
        web_growth = WebGrowthSystem(
            memory,
            firewall,
            config.web,
            config.synthetic.parameter_count,
            config.synthetic.parameter_groups,
        )
        synthetic = SyntheticThoughtEngine(
            parameter_count=config.synthetic.parameter_count,
            parameter_groups=config.synthetic.parameter_groups,
            context_vault_size=config.synthetic.context_vault_size,
            max_harvest_queries=config.synthetic.max_harvest_queries,
        )
        web_growth.register_additional_sources(synthetic.build_autonomous_sources())
        training = TrainingGround(memory)
        conversation = ConversationDatastore()
        language = LanguageEngine(GrammarDatastore())
        comprehension = MessageComprehender()
        speech_academy = SpeechAcademy()
        reasoning = ReasoningProfile()
        knowledge = KnowledgeGapMonitor()
        planner = DeliberativePlanner()
        knowledge_graph = KnowledgeGraph()
        retrieval = RetrievalManager(memory)
        coherence = CoherenceScorer()
        style = StyleProfile()
        evaluation = EvaluationHarness()
        critics = CriticSuite()
        orchestrator = ReasoningOrchestrator(
            planner,
            retrieval,
            knowledge_graph,
            coherence,
            style,
            evaluation,
            critics,
            default_trace_path=config.orchestrator.trace_path,
        )
        ollama_bridge = OllamaBridge(
            model=config.neural.ollama_model,
            timeout=config.neural.ollama_timeout,
        )
        distillation = DistillationCoach(memory, conversation, ollama_bridge)
        neural = UltraNeuralNetwork(
            parameter_count=config.neural.parameter_count,
            layers=config.neural.layers,
            ollama=ollama_bridge,
        )
        collective = NarrowCollective(
            specialists=[
                NarrowSpecialist("lexicon", ("hello", "hi", "greeting", "meaning")),
                NarrowSpecialist(
                    "reality",
                    ("human", "world", "experience", "time", "event"),
                    bias=0.7,
                ),
                NarrowSpecialist(
                    "coding",
                    ("lua", "roblox", "script", "function", "economy"),
                    bias=0.72,
                ),
                NarrowSpecialist(
                    "grammar",
                    ("sentence", "phrase", "syntax", "tone", "voice"),
                    bias=0.68,
                ),
            ]
        )
        cortex = Cortex(
            personality=personality,
            forge=forge,
            memory=memory,
            reflection=reflection,
            web_growth=web_growth,
            synthetic=synthetic,
            reasoning=reasoning,
            orchestrator=orchestrator,
        )
        kernel = Kernel(
            config=config,
            cortex=cortex,
            personality=personality,
            memory=memory,
            forge=forge,
            firewall=firewall,
            reflection=reflection,
            training=training,
            web_growth=web_growth,
            conversation=conversation,
            language=language,
            speech=speech_academy,
            comprehension=comprehension,
            synthetic=synthetic,
            reasoning=reasoning,
            knowledge=knowledge,
            neural=neural,
            collective=collective,
            distillation=distillation,
        )
        collaboration = CollaborationLayer(kernel)
        app = cls(config=config, kernel=kernel, collaboration=collaboration)
        kernel.bootstrap()
        return app

    def run_interactive(self) -> None:
        """Launch the Collaboration Layer in interactive mode."""
        self.collaboration.run_cli()

    def run_scripted(self, prompts: Iterable[str]) -> None:
        """Process a series of prompts without user interaction."""
        for prompt in prompts:
            stripped = prompt.strip()
            if not stripped:
                continue
            command = stripped.split(" ", 1)[0].lower()
            payload = stripped[len(command) :].strip()
            if command == "train":
                if not payload:
                    raise ValueError("Scripted training commands must include details.")
                self.kernel.enforce_security(command, payload)
                receipt = self.kernel.train(payload)
                self.collaboration.render_response(prompt, receipt.render())
                continue
            if command == "atrain":
                self.kernel.enforce_security(command, payload)
                if payload and payload.lower().startswith("once"):
                    focus = payload[4:].strip() or None
                    report = self.kernel.autonomous_train(focus)
                    self.collaboration.render_response(prompt, report.render())
                else:
                    status = self.kernel.start_autonomous_training(payload or None)
                    self.collaboration.render_response(prompt, status.render())
                continue
            if command == "stop":
                self.kernel.enforce_security(command, payload)
                status = self.kernel.stop_autonomous_training()
                self.collaboration.render_response(prompt, status.render())
                continue
            if command == "distill":
                self.kernel.enforce_security(command, payload)
                topic = payload or None
                receipt = self.kernel.distill(topic)
                self.collaboration.render_response(prompt, receipt.render())
                continue
            if command in {"talk", "chat"}:
                if not payload:
                    raise ValueError("Scripted talk commands must include a message.")
                self.kernel.enforce_security(command, payload)
                result = self.kernel.chat(payload)
                self.collaboration.render_response(prompt, result.render())
                continue
            if not self.kernel.permits_command(command):
                raise ValueError(f"Command '{command}' is not permitted in scripted mode.")
            self.kernel.enforce_security(command, payload)
            if command == "status":
                status = self.kernel.status()
                content = (
                    "System resources:\n"
                    + "\n".join(f"- {k}: {v}" for k, v in status.resources.items())
                    + f"\nPersonality: {status.personality}\n"
                    + "Memories:\n"
                    + (
                        "  (empty)"
                        if not status.memory_stats
                        else "\n".join(f"  {topic}: {count}" for topic, count in status.memory_stats.items())
                    )
                )
                self.collaboration.render_response(prompt, content)
                continue
            response = self.kernel.process_request(prompt)
            self.collaboration.render_response(prompt, response.render())
