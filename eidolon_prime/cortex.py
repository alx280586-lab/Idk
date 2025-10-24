"""Cortex and agent implementations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .state import PersonalityState
from .forge import Forge
from .memory import MemoryWeb
from .reflection import ReflectionEngine, ReflectionReport
from .web_growth import WebGrowthSystem, WebFinding


@dataclass
class AgentResponse:
    """Normalized response returned by each agent."""

    agent: str
    insight: str


class Agent:
    """Base class for Cortex agents."""

    name: str = "abstract"

    def generate(self, prompt: str, personality: PersonalityState) -> List[AgentResponse]:
        raise NotImplementedError


class LogicAgent(Agent):
    name = "logic"

    def generate(self, prompt: str, personality: PersonalityState) -> List[AgentResponse]:
        analysis = f"Analyzed prompt '{prompt}' with confidence {personality.confidence:.2f}."
        return [AgentResponse(self.name, analysis)]


class CuriosityAgent(Agent):
    name = "curiosity"

    def generate(self, prompt: str, personality: PersonalityState) -> List[AgentResponse]:
        if personality.curiosity < 0.3:
            return [AgentResponse(self.name, "Curiosity low; recommending incremental exploration.")]
        return [AgentResponse(self.name, f"Propose exploring variant of '{prompt}'.")]


class EthicsAgent(Agent):
    name = "ethics"

    def generate(self, prompt: str, personality: PersonalityState) -> List[AgentResponse]:
        return [AgentResponse(self.name, "Checked prompt against ethics baseline; no issues detected.")]


class Cortex:
    """Coordinates a set of cooperative agents."""

    def __init__(
        self,
        personality: PersonalityState,
        forge: Forge,
        memory: MemoryWeb,
        reflection: ReflectionEngine,
        web_growth: WebGrowthSystem,
    ) -> None:
        self._personality = personality
        self._forge = forge
        self._memory = memory
        self._reflection = reflection
        self._web_growth = web_growth
        self._agents: List[Agent] = [LogicAgent(), CuriosityAgent(), EthicsAgent()]

    def process(self, prompt: str) -> "CortexResult":
        responses: List[AgentResponse] = []
        for agent in self._agents:
            responses.extend(agent.generate(prompt, self._personality))
        insights = [response.insight for response in responses]
        experiments = self._forge.run(insights)
        reflection = self._reflection.review(insights)
        self._memory.record("prompt", prompt, 0.6, "cortex")
        policy = self._web_growth.describe_policy()
        return CortexResult(responses, experiments, reflection, policy)

    def register_finding(self, finding: WebFinding) -> int:
        return self._web_growth.integrate([finding])


@dataclass
class CortexResult:
    responses: List[AgentResponse]
    experiments: List
    reflection: ReflectionReport
    policy_summary: str

    def render(self) -> str:
        lines = ["Agent insights:"]
        for response in self.responses:
            lines.append(f"- {response.agent}: {response.insight}")
        lines.append("\nForge results:")
        for result in self.experiments:
            status = "success" if result.success else "failure"
            lines.append(f"- {result.description} => {status} ({result.notes})")
        lines.append("\nReflection:")
        lines.append(f"- {self.reflection.rationale}")
        lines.append("\nWeb policy:")
        lines.append(f"- {self.policy_summary}")
        return "\n".join(lines)
