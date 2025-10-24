"""Peer dialogue rehearsal that keeps the engine talking to other models."""
from __future__ import annotations

import random
import threading
from dataclasses import dataclass
from typing import List, Optional

from .config import PeerTrainingSettings
from .conversation import ConversationDatastore
from .distillation import DistillationCoach
from .memory import MemoryWeb
from .neural import UltraNeuralNetwork


@dataclass
class PeerDialogueReport:
    """Summary of a peer dialogue rehearsal cycle."""

    topic: str
    turns: int
    stored: int
    distilled: int
    highlights: List[str]

    def render(self) -> str:
        summary = (
            f"Peer dialogue on '{self.topic}' captured {self.turns} turns "
            f"with {self.stored} memory entries and {self.distilled} distilled lessons."
        )
        if self.highlights:
            summary += " Highlights: " + ", ".join(self.highlights[:4])
        return summary


class PeerDialogueTrainer:
    """Coordinates ongoing self-play conversations with external helpers."""

    def __init__(
        self,
        settings: PeerTrainingSettings,
        memory: MemoryWeb,
        conversation: ConversationDatastore,
        neural: UltraNeuralNetwork,
        distillation: DistillationCoach,
    ) -> None:
        self._settings = settings
        self._memory = memory
        self._conversation = conversation
        self._neural = neural
        self._distillation = distillation
        self._thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None

    # ------------------------------------------------------------------
    # Lifecycle controls
    # ------------------------------------------------------------------
    def bootstrap(self) -> Optional[PeerDialogueReport]:
        """Run a seed cycle so the datastore isn't empty at startup."""

        if not self._settings.enabled:
            return None
        default_topic = self._select_topic()
        return self.run_cycle(default_topic)

    def start_background(self) -> None:
        """Launch a daemon thread that keeps rehearsing with peers."""

        if not self._settings.enabled:
            return
        if self._thread and self._thread.is_alive():
            return
        stop_event = threading.Event()
        self._stop_event = stop_event

        def worker() -> None:
            index = 0
            topics = self._settings.topics or ["general conversation"]
            interval = max(0.5, self._settings.cycle_interval)
            while not stop_event.is_set():
                topic = topics[index % len(topics)]
                self.run_cycle(topic)
                index += 1
                stop_event.wait(interval)

        thread = threading.Thread(target=worker, name="eidolon-peer-dialogue", daemon=True)
        thread.start()
        self._thread = thread

    def stop_background(self) -> None:
        """Stop the background rehearsal loop if it is running."""

        if not self._thread or not self._thread.is_alive():
            return
        assert self._stop_event is not None
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None
        self._stop_event = None

    def is_running(self) -> bool:
        thread = self._thread
        return bool(thread and thread.is_alive())

    # ------------------------------------------------------------------
    # Dialogue generation
    # ------------------------------------------------------------------
    def run_cycle(self, topic: Optional[str] = None) -> PeerDialogueReport:
        """Execute a single rehearsal loop against the neural mesh."""

        focus = topic or self._select_topic()
        turns = max(2, self._settings.conversation_turns)
        utterances = self._neural.self_dialogue(focus, turns=turns)
        highlights: List[str] = []
        stored = 0
        for idx, utterance in enumerate(utterances, start=1):
            marker = f"peer_dialogue::{focus}::turn{idx:02d}"
            self._memory.record(marker, utterance, 0.62, "peer_dialogue")
            highlights.append(marker)
            stored += 1
        if highlights:
            self._conversation.ingest_highlights(
                (marker, marker.replace("peer_dialogue::", ""), utterance)
                for marker, utterance in zip(highlights, utterances)
            )
        distilled = 0
        if self._settings.distillation_limit > 0:
            distilled = self._distillation.run(focus, limit=self._settings.distillation_limit)
        return PeerDialogueReport(focus, turns, stored, distilled, highlights)

    def observe_dialogue(self, prompt: str, reply: str, reasoning_trace: str) -> None:
        """Record a real conversation so peer rehearsal stays aligned."""

        if not self._settings.enabled:
            return
        content = (
            f"Prompt: {prompt}\nReply: {reply}\nReasoning: {reasoning_trace[:320]}"
        )
        self._memory.record("peer_dialogue::observation", content, 0.58, "peer_dialogue_observation")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _select_topic(self) -> str:
        if not self._settings.topics:
            return "general conversation"
        return random.choice(self._settings.topics)


__all__ = ["PeerDialogueReport", "PeerDialogueTrainer"]
