"""Planner agent responsible for decomposing tasks into actionable steps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .memory import MemoryStore
from .tools import LocalLLM


@dataclass
class Plan:
    task_id: int
    steps: List[str]


class Planner:
    """Simple rule-driven planner using the local LLaMA stub."""

    def __init__(self, llm: LocalLLM, memory: MemoryStore) -> None:
        self.llm = llm
        self.memory = memory

    def create_plan(self, task_id: int, description: str) -> Plan:
        prompt = (
            "You are a planner agent for a Roblox automation system. "
            "Break down the task into high-level steps."
        )
        _ = self.llm.complete(prompt + "\n" + description)

        # For deterministic behaviour we use a handcrafted recipe keyed on
        # keywords found in the description. This keeps the framework
        # self-contained without an actual language model.
        steps: List[str]
        if "radar" in description.lower():
            steps = [
                "Study memory for existing radar rendering snippets.",
                "Draft Lua script scaffolding with service acquisition.",
                "Implement Perlin noise driven pixel grid rendering.",
                "Add randomized swirl dynamics and logging.",
                "Prepare summary for critic evaluation.",
            ]
        else:
            steps = [
                "Collect related skills from memory.",
                "Outline Roblox services to use.",
                "Draft core Lua functions.",
                "Review script for performance and API compliance.",
            ]

        self.memory.log_plan(task_id, steps)
        return Plan(task_id=task_id, steps=steps)
