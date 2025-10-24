"""Conversational distillation pipeline for improved language quality."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from .memory import MemoryWeb
from .conversation import ConversationDatastore, ConversationPattern
from .ollama import OllamaBridge


@dataclass(frozen=True)
class DistillationDialogue:
    """A curated exemplar used to strengthen conversational style."""

    topic: str
    prompt: str
    response: str
    tone: str = "warm"
    structure: str = "clarify→answer→invite"
    register: str = "technical_conversational"


_DISTILLATION_DIALOGUES: Tuple[DistillationDialogue, ...] = (
    DistillationDialogue(
        topic="smalltalk.greeting",
        prompt="Hi there, how's your day going?",
        response=(
            "Hi! I'm having a productive day digging into new ideas. "
            "How's your day unfolding?"
        ),
        tone="friendly",
        structure="greet→explore→respond→reflect",
        register="dialogue_support",
    ),
    DistillationDialogue(
        topic="roblox.overview",
        prompt="What do you know about Roblox development?",
        response=(
            "Roblox development blends Lua scripting with the Studio toolset. "
            "You model worlds, attach behaviours through Luau scripts, and publish "
            "experiences that scale automatically in the cloud."
        ),
        tone="steady",
        structure="acknowledge→analysis→summary",
        register="engineering",
    ),
    DistillationDialogue(
        topic="essay.structure",
        prompt="Could you write a short essay about balanced game economies?",
        response=(
            "A balanced game economy respects player time and creates meaningful choices. "
            "Designers monitor sinks and sources, run live telemetry experiments, and adjust "
            "rewards before scarcity or inflation erodes trust."
        ),
        tone="reflective",
        structure="thesis→support→synthesis→next-step",
        register="essay_formal",
    ),
)


class DistillationCoach:
    """Generates distilled conversational lessons and stores them for reuse."""

    def __init__(
        self,
        memory: MemoryWeb,
        conversation: ConversationDatastore,
        ollama: Optional[OllamaBridge] = None,
    ) -> None:
        self._memory = memory
        self._conversation = conversation
        self._ollama = ollama

    def run(self, topic: Optional[str] = None, *, limit: int = 6) -> int:
        """Populate memory and conversation datastore with distilled dialogues."""

        lessons = list(self._seed_dialogues(topic))
        if self._ollama and self._ollama.available():
            lessons.extend(self._ollama_dialogues(topic, remaining=max(0, limit - len(lessons))))
        stored = 0
        for dialogue in lessons[:limit]:
            self._memory.record(
                topic=f"distillation::{dialogue.topic}",
                content=f"Prompt: {dialogue.prompt}\nResponse: {dialogue.response}",
                confidence=0.72,
                provenance="distillation", 
            )
            self._register_pattern(dialogue)
            stored += 1
        return stored

    def _seed_dialogues(self, topic: Optional[str]) -> Iterable[DistillationDialogue]:
        if not topic:
            yield from _DISTILLATION_DIALOGUES
            return
        lowered = topic.lower()
        for dialogue in _DISTILLATION_DIALOGUES:
            if lowered in dialogue.topic.lower() or lowered in dialogue.prompt.lower():
                yield dialogue

    def _register_pattern(self, dialogue: DistillationDialogue) -> None:
        pattern_id = f"distill::{dialogue.topic}"
        if self._conversation.get_pattern(pattern_id):
            return
        pattern = ConversationPattern(
            pattern_id=pattern_id,
            intent="conversation",
            tone=dialogue.tone,
            structure=dialogue.structure,
            register=dialogue.register,
            success_score_by_context={"global": 0.66},
        )
        self._conversation.add_pattern(pattern)

    def _ollama_dialogues(
        self, topic: Optional[str], *, remaining: int
    ) -> Iterable[DistillationDialogue]:
        if remaining <= 0:
            return []
        prompts: List[str] = []
        if topic:
            prompts.append(
                "Write a friendly two-sentence reply to a user asking about "
                f"{topic}. Focus on clarity and warmth."
            )
        prompts.extend(
            [
                "Craft a concise explanation of a Roblox scripting best practice in two sentences.",
                "Give a short essay-style reflection about how developers stay current with technology news.",
            ]
        )
        dialogues: List[DistillationDialogue] = []
        for prompt_text in prompts[:remaining]:
            result = self._ollama.suggest_summary(prompt_text)
            if not result:
                continue
            dialogues.append(
                DistillationDialogue(
                    topic=f"ollama::{prompt_text[:24].strip().lower().replace(' ', '_')}",
                    prompt=prompt_text,
                    response=result.strip(),
                    tone="balanced",
                    structure="acknowledge→analysis→summary",
                    register="technical_conversational",
                )
            )
        return dialogues


__all__ = ["DistillationCoach"]
