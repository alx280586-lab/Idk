"""Cortex and agent implementations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .state import PersonalityState
from .forge import Forge
from .memory import MemoryWeb, MemoryEntry
from .reflection import ReflectionEngine, ReflectionReport
from .web_growth import WebGrowthSystem, WebFinding
from .synthetic import SyntheticThoughtEngine, SyntheticThoughtPlan
from .comprehension import MessageUnderstanding


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
        context: Optional[Dict[str, object]] = None,
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
        context: Optional[Dict[str, object]] = None,
    ) -> List[AgentResponse]:
        if related:
            domain = related[0].topic.split("::")[0]
            analysis = (
                f"Mapped your request to {domain} patterns while keeping confidence"
                f" at {personality.confidence:.2f}."
            )
        else:
            focus_text = None
            if context:
                understanding = context.get("understanding")
                if isinstance(understanding, MessageUnderstanding) and understanding.focus_terms:
                    focus_text = ", ".join(understanding.focus_terms[:4])
            if focus_text:
                analysis = (
                    f"Structured your full message around {focus_text}"
                    f" with confidence {personality.confidence:.2f}."
                )
            else:
                analysis = (
                    f"Structured the prompt '{prompt}' into actionable checkpoints"
                    f" with confidence {personality.confidence:.2f}."
                )
        return [AgentResponse(self.name, analysis)]


class CuriosityAgent(Agent):
    name = "curiosity"

    def generate(
        self,
        prompt: str,
        personality: PersonalityState,
        memory: MemoryWeb,
        related: List[MemoryEntry],
        context: Optional[Dict[str, object]] = None,
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
        context: Optional[Dict[str, object]] = None,
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
        context: Optional[Dict[str, object]] = None,
    ) -> List[AgentResponse]:
        lowered = prompt.lower().strip()
        understanding: Optional[MessageUnderstanding] = None
        plan: Optional[SyntheticThoughtPlan] = None
        if context:
            candidate = context.get("understanding")
            if isinstance(candidate, MessageUnderstanding):
                understanding = candidate
            plan_candidate = context.get("synthetic_plan")
            if isinstance(plan_candidate, SyntheticThoughtPlan):
                plan = plan_candidate
        tokens = _keywords(lowered)
        steps: List[str] = []
        if _looks_like_greeting(lowered):
            steps.append("Recognised your greeting and will mirror a warm tone before digging deeper.")
        if understanding and understanding.question:
            steps.append("Flagged the request as a question so I outline the answer before offering experiments.")
        if related:
            steps.append(_summarize_related_memories(related))
        else:
            preview = ", ".join(tokens[:4]) if tokens else "the core idea"
            steps.append(
                f"No stored lesson matched directly, so I'm lining up autonomous web search and practice drills around {preview}."
            )
        if understanding and understanding.focus_terms:
            focus_statement = ", ".join(understanding.focus_terms[:5])
            steps.append(
                f"I analysed every word and mapped the core terms to {focus_statement}."
            )
        if understanding and understanding.focus_pairs:
            pair_statement = ", ".join(understanding.focus_pairs[:3])
            steps.append(
                f"Key phrases combined into: {pair_statement}, giving me sentence-level intent."
            )
        if understanding and understanding.command_clauses:
            steps.append(
                "Detected direct requests such as "
                + "; ".join(understanding.command_clauses[:2])
                + " and will respond to each explicitly."
            )
        if plan:
            steps.append(
                "Synthetic thought engine recommended "
                + ", ".join(trace.module for trace in plan.module_traces[:3])
                + " to keep reasoning exhaustive."
            )
            if plan.outline:
                steps.append(plan.outline[0])
        reasoning_tracks = [entry for entry in related if entry.topic.startswith("reasoning::")]
        if reasoning_tracks:
            focus = reasoning_tracks[0].topic.split("::")[1:4]
            steps.append(
                "Following reasoning blueprint "
                + " → ".join(part.replace("_", " ") for part in focus)
                + " to keep thoughts organised."
            )
        interaction_examples = [entry for entry in related if entry.topic.startswith("interaction::")]
        if interaction_examples:
            steps.append("Referencing interaction transcripts so tone and pacing mirror successful dialogues.")
        if any(entry.provenance == "speech_practice" for entry in related):
            steps.append("Recent speech rehearsals give me phrasing patterns that keep the reply natural.")
        if personality.curiosity < 0.4:
            steps.append("I'll raise curiosity slightly so we test assumptions instead of echoing keywords.")
        if not reasoning_tracks:
            steps.append(
                "I'll synthesise a mini plan: clarify intent, surface relevant knowledge, weigh trade-offs, and confirm next steps."
            )
        if understanding and understanding.urgency:
            steps.append("User phrasing signalled urgency, so I'll move faster on verification.")
        narrative = " ".join(steps)
        conclusion = "That plan shapes a grounded response that stays relevant to what you asked."
        return [AgentResponse(self.name, f"{narrative} {conclusion}")]


class SyntheticAgent(Agent):
    name = "synthetic"

    def generate(
        self,
        prompt: str,
        personality: PersonalityState,
        memory: MemoryWeb,
        related: List[MemoryEntry],
        context: Optional[Dict[str, object]] = None,
    ) -> List[AgentResponse]:
        if not context:
            return [AgentResponse(self.name, "Synthetic modules idle; no context supplied.")]
        plan = context.get("synthetic_plan")
        if not isinstance(plan, SyntheticThoughtPlan):
            return [AgentResponse(self.name, "Synthetic plan not available for this turn.")]
        headline = plan.summary()
        outline = plan.outline[:2]
        detail = " ".join(outline) if outline else "Preparing baseline outline."
        harvest_hint = (
            f" Target web harvest: {', '.join(plan.harvest_queries[:2])}."
            if plan.harvest_queries
            else ""
        )
        return [
            AgentResponse(
                self.name,
                f"{headline}. {detail}{harvest_hint}",
            )
        ]


def _keywords(text: str) -> List[str]:
    parts = [token.strip(".,!?;:") for token in text.split() if len(token) > 3]
    seen = []
    for part in parts:
        if part not in seen:
            seen.append(part)
    return seen


def _looks_like_greeting(text: str) -> bool:
    greetings = {"hello", "hi", "hey", "greetings", "good morning", "good evening"}
    return any(text.startswith(greet) for greet in greetings)


def _summarize_related_memories(related: List[MemoryEntry]) -> str:
    domains = {}
    snippets: List[str] = []
    for entry in related[:4]:
        head = entry.topic.split("::")[0]
        domains[head] = domains.get(head, 0) + 1
        snippet = entry.content
        if len(snippet) > 90:
            snippet = snippet[:87] + "..."
        snippets.append(f"{head} → {snippet}")
    focus_domains = ", ".join(f"{domain}×{count}" for domain, count in sorted(domains.items(), key=lambda item: item[1], reverse=True))
    evidence = "; ".join(snippets)
    return f"Mapped {len(related)} supporting memories ({focus_domains}) and will weave in evidence such as {evidence}."


class Cortex:
    """Coordinates a set of cooperative agents."""

    def __init__(
        self,
        personality: PersonalityState,
        forge: Forge,
        memory: MemoryWeb,
        reflection: ReflectionEngine,
        web_growth: WebGrowthSystem,
        synthetic: SyntheticThoughtEngine,
    ) -> None:
        self._personality = personality
        self._forge = forge
        self._memory = memory
        self._reflection = reflection
        self._web_growth = web_growth
        self._synthetic = synthetic
        self._agents: List[Agent] = [
            LogicAgent(),
            CuriosityAgent(),
            EthicsAgent(),
            SyntheticAgent(),
            ReasoningAgent(),
        ]

    def process(
        self,
        prompt: str,
        understanding: Optional[MessageUnderstanding] = None,
        plan: Optional[SyntheticThoughtPlan] = None,
    ) -> "CortexResult":
        responses: List[AgentResponse] = []
        query = prompt
        if understanding:
            focus_text = understanding.focus_text()
            if focus_text:
                query = f"{prompt} || {focus_text}"
        related = self._memory.search(query, limit=7)
        generated_plan = plan
        if generated_plan is None and understanding is not None:
            generated_plan = self._synthetic.plan(prompt, understanding, self._memory)
        plan = generated_plan
        if len(related) < 3:
            focus = understanding.focus_text() if understanding else prompt
            report = self._web_growth.autonomous_training(focus, batch_size=10)
            self._memory.record(
                "cortex::auto_refresh",
                report.render(),
                0.66,
                "autonomous_web",
            )
            related = self._memory.search(query, limit=9)
        context: Dict[str, object] = {}
        if understanding:
            context["understanding"] = understanding
        if plan:
            context["synthetic_plan"] = plan
        for agent in self._agents:
            responses.extend(
                agent.generate(
                    prompt,
                    self._personality,
                    self._memory,
                    related,
                    context,
                )
            )
        insights = [response.insight for response in responses]
        experiments = self._forge.run(insights)
        reflection = self._reflection.review(insights)
        self._memory.record("prompt", prompt, 0.6, "cortex")
        policy = self._web_growth.describe_policy()
        reasoning_summary = self._summarize_reasoning(
            prompt, related, experiments, understanding, plan
        )
        return CortexResult(responses, experiments, reflection, policy, related, reasoning_summary)

    def _summarize_reasoning(
        self,
        prompt: str,
        related: List[MemoryEntry],
        experiments: List,
        understanding: Optional[MessageUnderstanding] = None,
        plan: Optional[SyntheticThoughtPlan] = None,
    ) -> str:
        if not related:
            if understanding and understanding.focus_terms:
                focus = ", ".join(understanding.focus_terms[:4])
                return (
                    "I am exploring the prompt without a direct precedent in memory, "
                    f"so I'm leaning on your highlighted terms: {focus}."
                )
            summary = "I am exploring the prompt without a direct precedent in memory."
            if plan:
                summary += " Synthetic modules keep the plan structured despite the gap."
            return summary
        dominant_topics = {}
        for entry in related:
            head = entry.topic.split("::")[0]
            dominant_topics[head] = dominant_topics.get(head, 0) + 1
        ordered = sorted(dominant_topics.items(), key=lambda item: item[1], reverse=True)
        focus_domain = ordered[0][0]
        experiment_summary = " and ".join(result.description for result in experiments[:2]) if experiments else "baseline heuristics"
        detail = ""
        if understanding and understanding.focus_pairs:
            detail = (
                " I also preserved your phrasing focus around "
                + ", ".join(understanding.focus_pairs[:3])
                + "."
            )
        synthetic_clause = ""
        if plan:
            synthetic_clause = (
                " Synthetic plan engaged modules "
                + ", ".join(trace.module for trace in plan.module_traces[:3])
                + " and recommended "
                + (plan.outline[0] if plan.outline else "a verification loop")
                + "."
            )
        return (
            f"I mapped your prompt '{prompt}' to the domain '{focus_domain}' using the strongest training overlaps. "
            f"Experiments such as {experiment_summary} confirm that the retrieved lessons align with your request.{detail}"\
            f"{synthetic_clause}"
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
