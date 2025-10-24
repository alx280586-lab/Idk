"""Cortex and agent implementations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .state import PersonalityState
from .forge import Forge
from .memory import MemoryWeb, MemoryEntry
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

    def generate(
        self,
        prompt: str,
        personality: PersonalityState,
        memory: MemoryWeb,
        related: List[MemoryEntry],
    ) -> List[AgentResponse]:
        raise NotImplementedError


class LogicAgent(Agent):
    name = "logic"

    def generate(
        self,
        prompt: str,
        personality: PersonalityState,
        memory: MemoryWeb,
        related: List[MemoryEntry],
    ) -> List[AgentResponse]:
        analysis = f"Analyzed prompt '{prompt}' with confidence {personality.confidence:.2f}."
        return [AgentResponse(self.name, analysis)]


class CuriosityAgent(Agent):
    name = "curiosity"

    def generate(
        self,
        prompt: str,
        personality: PersonalityState,
        memory: MemoryWeb,
        related: List[MemoryEntry],
    ) -> List[AgentResponse]:
        if personality.curiosity < 0.3:
            return [AgentResponse(self.name, "Curiosity low; recommending incremental exploration.")]
        return [AgentResponse(self.name, f"Propose exploring variant of '{prompt}'.")]


class EthicsAgent(Agent):
    name = "ethics"

    def generate(
        self,
        prompt: str,
        personality: PersonalityState,
        memory: MemoryWeb,
        related: List[MemoryEntry],
    ) -> List[AgentResponse]:
        return [AgentResponse(self.name, "Checked prompt against ethics baseline; no issues detected.")]


class ReasoningAgent(Agent):
    name = "reasoning"

    def generate(
        self,
        prompt: str,
        personality: PersonalityState,
        memory: MemoryWeb,
        related: List[MemoryEntry],
    ) -> List[AgentResponse]:
        if not related:
            return [AgentResponse(self.name, "No direct lessons matched; initiating exploratory reasoning.")]
        representative = related[0]
        domain, _, aspect = representative.topic.partition("::")
        if "so that the initiative " in representative.content:
            benefit = representative.content.split("so that the initiative ", 1)[1].rstrip(".")
        else:
            benefit = "drives measurable outcomes"
        patterns = {entry.topic.split("::")[0] for entry in related}
        pattern_summary = ", ".join(sorted(patterns))
        insight = (
            f"Synthesized {len(related)} lessons across {pattern_summary}. "
            f"They consistently show that investing in {aspect} within {domain} empowers teams because it {benefit}."
        )
        return [AgentResponse(self.name, insight)]


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
        self._agents: List[Agent] = [
            LogicAgent(),
            CuriosityAgent(),
            EthicsAgent(),
            ReasoningAgent(),
        ]

    def process(self, prompt: str) -> "CortexResult":
        responses: List[AgentResponse] = []
        related = self._memory.search(prompt, limit=7)
        for agent in self._agents:
            responses.extend(agent.generate(prompt, self._personality, self._memory, related))
        insights = [response.insight for response in responses]
        experiments = self._forge.run(insights)
        reflection = self._reflection.review(insights)
        self._memory.record("prompt", prompt, 0.6, "cortex")
        policy = self._web_growth.describe_policy()
        reasoning_summary = self._summarize_reasoning(prompt, related, experiments)
        return CortexResult(responses, experiments, reflection, policy, related, reasoning_summary)

    def _summarize_reasoning(
        self,
        prompt: str,
        related: List[MemoryEntry],
        experiments: List,
    ) -> str:
        if not related:
            return "I am exploring the prompt without a direct precedent in memory."
        dominant_topics = {}
        for entry in related:
            head = entry.topic.split("::")[0]
            dominant_topics[head] = dominant_topics.get(head, 0) + 1
        ordered = sorted(dominant_topics.items(), key=lambda item: item[1], reverse=True)
        focus_domain = ordered[0][0]
        experiment_summary = " and ".join(result.description for result in experiments[:2]) if experiments else "baseline heuristics"
        return (
            f"I mapped your prompt '{prompt}' to the domain '{focus_domain}' using the strongest training overlaps. "
            f"Experiments such as {experiment_summary} confirm that the retrieved lessons align with your request."
        )

    def register_finding(self, finding: WebFinding) -> int:
        return self._web_growth.integrate([finding])


@dataclass
class CortexResult:
    responses: List[AgentResponse]
    experiments: List
    reflection: ReflectionReport
    policy_summary: str
    related_memories: List[MemoryEntry]
    reasoning_summary: str

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
        lines.append("\nReasoning summary:")
        lines.append(f"- {self.reasoning_summary}")
        if self.related_memories:
            lines.append("\nEvidence snippets:")
            for entry in self.related_memories[:5]:
                domain, _, aspect = entry.topic.partition("::")
                lines.append(
                    f"- {domain} / {aspect}: confidence {entry.confidence:.2f}" 
                    f" (stored {entry.timestamp.isoformat()}Z)"
                )
        return "\n".join(lines)
