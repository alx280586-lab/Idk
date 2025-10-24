"""Synthetic Thought Engine implementing procedural cognitive modules."""
from __future__ import annotations

import math
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Sequence, Tuple

from .comprehension import MessageUnderstanding
from .memory import MemoryWeb


@dataclass
class ModuleTrace:
    """Record of how a procedural module influenced the current plan."""

    module: str
    category: str
    mechanism: str
    focus: str
    rationale: str
    score: float

    def render(self) -> str:
        return (
            f"{self.module} ({self.category}) → {self.mechanism} around {self.focus}"
            f" [{self.score:.2f}] — {self.rationale}"
        )


@dataclass
class SyntheticThoughtPlan:
    """Structured blueprint returned by the synthetic thought engine."""

    focus_terms: List[str]
    focus_pairs: List[str]
    outline: List[str]
    module_traces: List[ModuleTrace]
    harvest_queries: List[str]
    parameter_snapshot: Dict[str, float]
    context_links: List[str]
    style_hint: str

    def summary(self) -> str:
        focus_text = ", ".join(self.focus_pairs or self.focus_terms[:4]) or "conversation"
        return (
            f"Focus: {focus_text} | Modules: "
            + ", ".join(trace.module for trace in self.module_traces[:4])
        )

    def render(self) -> str:
        lines = [
            "Synthetic Thought Plan",
            "----------------------",
            f"Focus terms: {', '.join(self.focus_terms) or 'n/a'}",
            f"Focus pairs: {', '.join(self.focus_pairs) or 'n/a'}",
            f"Style hint: {self.style_hint}",
            "Outline:",
        ]
        if self.outline:
            for step in self.outline:
                lines.append(f"  • {step}")
        else:
            lines.append("  • Establish baseline understanding before replying.")
        if self.module_traces:
            lines.append("Modules engaged:")
            for trace in self.module_traces:
                lines.append(f"  • {trace.render()}")
        if self.harvest_queries:
            lines.append("Recommended web harvest queries:")
            for query in self.harvest_queries:
                lines.append(f"  • {query}")
        if self.context_links:
            lines.append("Context vault references:")
            for link in self.context_links[:6]:
                lines.append(f"  • {link}")
        if self.parameter_snapshot:
            lines.append("Parameter snapshot:")
            for key, value in self.parameter_snapshot.items():
                lines.append(f"  • {key}: {value:.3f}")
        return "\n".join(lines)


@dataclass
class ProceduralModule:
    """Lightweight description of a procedural reasoning module."""

    name: str
    category: str
    mechanism: str
    description: str
    keywords: Tuple[str, ...]
    base_weight: float

    def evaluate(
        self,
        understanding: MessageUnderstanding,
        context_links: Sequence[str],
        parameter_bias: float,
    ) -> Optional[ModuleTrace]:
        tokens = Counter(understanding.tokens)
        match_strength = sum(tokens.get(keyword, 0) for keyword in self.keywords)
        focus_candidates = [
            term
            for term in understanding.focus_terms
            if any(keyword in term.lower() for keyword in self.keywords)
        ]
        focus = focus_candidates[0] if focus_candidates else (understanding.topic_hint())
        if match_strength == 0 and parameter_bias < 0.35:
            return None
        influence = self.base_weight + 0.08 * match_strength + parameter_bias * 0.2
        rationale_bits = []
        if match_strength:
            rationale_bits.append(
                f"matched focus terms ({', '.join(self.keywords[:3])})"
            )
        if context_links:
            rationale_bits.append("context vault support available")
        if parameter_bias > 0.5:
            rationale_bits.append("entropy bias encourages exploration")
        if not rationale_bits:
            rationale_bits.append("acts as a balancing module")
        rationale = ", ".join(rationale_bits)
        return ModuleTrace(
            module=self.name,
            category=self.category,
            mechanism=self.mechanism,
            focus=focus,
            rationale=rationale,
            score=min(1.0, influence),
        )


class ContextVault:
    """Ephemeral cache that stores recent comprehension artefacts."""

    def __init__(self, capacity: int = 320) -> None:
        self._entries: Deque[Tuple[float, str, Tuple[str, ...]]] = deque(maxlen=capacity)

    def remember(self, message: str, understanding: MessageUnderstanding) -> None:
        focus = tuple(understanding.focus_terms[:6])
        timestamp = time.time()
        self._entries.append((timestamp, message, focus))

    def related(self, understanding: MessageUnderstanding) -> List[str]:
        targets = set(understanding.focus_terms[:6])
        highlights: List[str] = []
        for timestamp, message, focus_terms in reversed(self._entries):
            if not focus_terms:
                continue
            overlap = targets.intersection(focus_terms)
            if overlap:
                age_seconds = max(1.0, time.time() - timestamp)
                freshness = max(0.1, min(1.0, 1.0 / math.log(age_seconds + 2)))
                overlap_text = ", ".join(sorted(overlap))
                highlights.append(
                    f"{overlap_text} ↔ '{message[:72]}...' (freshness {freshness:.2f})"
                )
            if len(highlights) >= 8:
                break
        return highlights


class ParameterTuner:
    """Simulated micro-parameter bank that nudges procedural modules."""

    def __init__(self, parameter_count: int, groups: int = 8) -> None:
        self._parameter_count = parameter_count
        self._group_count = max(1, groups)
        self._entropy_bias = 0.4
        self._precision_bias = 0.6
        self._symbolic_bias = 0.5
        self._group_biases: List[float] = [0.5 for _ in range(self._group_count)]
        self._last_snapshot: Dict[str, float] = {}

    def calibrate(
        self,
        message_length: int,
        vocabulary_size: int,
        question: bool,
    ) -> Dict[str, float]:
        entropy_adjust = min(0.4, vocabulary_size / 40.0)
        self._entropy_bias = 0.35 + entropy_adjust
        if question:
            self._precision_bias = 0.68
        else:
            self._precision_bias = 0.55 + min(0.2, message_length / 240.0)
        self._symbolic_bias = 0.48 + min(0.25, vocabulary_size / 120.0)
        for index in range(self._group_count):
            phase = (message_length * (index + 1) + vocabulary_size) % 17
            self._group_biases[index] = 0.38 + 0.22 * math.sin(phase / 5.0)
        snapshot: Dict[str, float] = {
            "parameters": float(self._parameter_count),
            "group_count": float(self._group_count),
            "entropy_bias": self._entropy_bias,
            "precision_bias": self._precision_bias,
            "symbolic_bias": self._symbolic_bias,
        }
        for idx, bias in enumerate(self._group_biases, start=1):
            snapshot[f"group_bias_{idx}"] = bias
        self._last_snapshot = snapshot
        return self._last_snapshot

    @property
    def entropy_bias(self) -> float:
        return self._entropy_bias

    def snapshot(self) -> Dict[str, float]:
        return dict(self._last_snapshot)

    def bias_for_module(self, module_index: int) -> float:
        if not self._group_biases:
            return self._entropy_bias
        return self._group_biases[module_index % self._group_count]


@dataclass(frozen=True)
class ProceduralKnowledgeField:
    """Descriptor for generating procedural knowledge snippets."""

    domain: str
    generator: str
    descriptors: Tuple[str, ...]

    def synthesize(self, seed: str, aspect: str, weight: float) -> Tuple[str, str, float, str]:
        topic = f"synthetic::{self.domain}::{seed.replace(' ', '_')}::{aspect.replace(' ', '_')}"
        content = (
            f"{self.generator} for {seed} emphasises {aspect}."
            f" Practise by {self.descriptors[0]} and validate via {self.descriptors[-1]}."
        )
        confidence = 0.72 + min(0.18, weight)
        return topic, content, confidence, "synthetic_datastore"


class SyntheticThoughtEngine:
    """Central coordinator for the procedural + parametric hybrid model."""

    def __init__(
        self,
        parameter_count: int = 3_200_000,
        *,
        parameter_groups: int = 16,
        context_vault_size: int = 320,
        max_harvest_queries: int = 3,
    ) -> None:
        self._modules: List[ProceduralModule] = _build_modules()
        self._vault = ContextVault(capacity=context_vault_size)
        self._parameters = ParameterTuner(parameter_count, groups=parameter_groups)
        self._knowledge_fields: Tuple[ProceduralKnowledgeField, ...] = _build_knowledge_fields()
        self._max_harvest_queries = max_harvest_queries
        self._seeded = False

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------
    def plan(
        self,
        message: str,
        understanding: MessageUnderstanding,
        memory: MemoryWeb,
    ) -> SyntheticThoughtPlan:
        self._vault.remember(message, understanding)
        snapshot = self._parameters.calibrate(
            len(message), len(set(understanding.tokens)), understanding.question
        )
        context_links = self._vault.related(understanding)
        module_traces: List[ModuleTrace] = []
        for index, module in enumerate(self._modules):
            trace = module.evaluate(
                understanding,
                context_links,
                self._parameters.bias_for_module(index),
            )
            if trace:
                module_traces.append(trace)
        module_traces.sort(key=lambda trace: trace.score, reverse=True)
        if not module_traces:
            module_traces.append(
                ModuleTrace(
                    module="Baseline Planner",
                    category="stabiliser",
                    mechanism="review prior lessons and echo comprehension summary",
                    focus=understanding.topic_hint(),
                    rationale="no specialist module triggered; falling back to baseline",
                    score=0.55,
                )
            )
        outline = self._compose_outline(module_traces, understanding)
        harvest_queries = self._propose_harvest_queries(module_traces, understanding, memory)
        style_hint = self._style_hint(module_traces, understanding)
        return SyntheticThoughtPlan(
            focus_terms=list(understanding.focus_terms[:10]),
            focus_pairs=list(understanding.focus_pairs[:8]),
            outline=outline,
            module_traces=module_traces,
            harvest_queries=harvest_queries,
            parameter_snapshot=snapshot,
            context_links=context_links,
            style_hint=style_hint,
        )

    def observe_training_report(self, summary: str) -> None:
        understanding = MessageUnderstanding(
            original=summary,
            sentences=[summary],
            tokens=summary.lower().split(),
            keywords=summary.lower().split(),
            focus_terms=summary.lower().split()[:6],
            focus_pairs=[],
            question=False,
            affect="neutral",
            urgency=False,
            command_clauses=[],
        )
        self._vault.remember(summary, understanding)

    # ------------------------------------------------------------------
    # Knowledge seeding
    # ------------------------------------------------------------------
    def seed_memory(self, memory: MemoryWeb) -> Dict[str, int]:
        if self._seeded:
            return {}
        grammar_topics = _GRAMMAR_TOPICS
        conversation_arcs = _CONVERSATION_ARCS
        coding_moves = _CODING_MOVES
        payload: List[Tuple[str, str, float, str]] = []
        count_grammar = 0
        count_conversation = 0
        count_coding = 0
        for idx, rule in enumerate(grammar_topics):
            for aspect in ("agreement", "variation", "clarity", "flow"):
                knowledge_field = self._knowledge_fields[0]
                payload.append(
                    knowledge_field.synthesize(rule, aspect, 0.15 + (idx % 7) * 0.03)
                )
                count_grammar += 1
        for idx, arc in enumerate(conversation_arcs):
            for aspect in ("tone", "intent", "repair", "empathy", "evidence"):
                knowledge_field = self._knowledge_fields[1]
                payload.append(
                    knowledge_field.synthesize(arc, aspect, 0.12 + (idx % 5) * 0.02)
                )
                count_conversation += 1
        for idx, move in enumerate(coding_moves):
            for aspect in ("safety", "performance", "robustness", "testing"):
                knowledge_field = self._knowledge_fields[2]
                payload.append(
                    knowledge_field.synthesize(move, aspect, 0.18 + (idx % 6) * 0.025)
                )
                count_coding += 1
        memory.bulk_record(payload)
        self._seeded = True
        return {
            "grammar": count_grammar,
            "conversation": count_conversation,
            "coding": count_coding,
        }

    # ------------------------------------------------------------------
    # Web growth integration
    # ------------------------------------------------------------------
    def build_autonomous_sources(self) -> List[object]:
        from .web_growth import AutonomousSource

        sources: List[AutonomousSource] = []
        for domain, tier, summary in _SYNTHETIC_DOMAINS:
            for idx, topic in enumerate(_SYNTHETIC_TOPIC_CLUSTERS):
                slug = topic.replace(" ", "-")
                url = f"{domain}/knowledge/{idx:04d}-{slug}"
                insight = f"Procedural insight on {topic} synthesised from {domain}."
                tags = ("Synthetic", slug, tier, "web-crawl")
                sources.append(
                    AutonomousSource(
                        source=url,
                        topic=f"synthetic::{slug}",
                        insight=insight,
                        summary=f"{summary} covering {topic}.",
                        tags=tags,
                        tier=tier,
                        refresh_days=7 if tier == "S" else 21,
                    )
                )
        return sources

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _compose_outline(
        self,
        traces: Sequence[ModuleTrace],
        understanding: MessageUnderstanding,
    ) -> List[str]:
        outline: List[str] = []
        if understanding.focus_pairs:
            outline.append(
                f"Map the sentence links {', '.join(understanding.focus_pairs[:3])}"
                " into a shared context."
            )
        for trace in traces[:4]:
            outline.append(
                f"Apply {trace.module} to {trace.mechanism} while centring {trace.focus}."
            )
        outline.append(
            "Run a self-critique loop to ensure tone, evidence, and actions align with the request."
        )
        return outline

    def _propose_harvest_queries(
        self,
        traces: Sequence[ModuleTrace],
        understanding: MessageUnderstanding,
        memory: MemoryWeb,
    ) -> List[str]:
        suggestions: List[str] = []
        focus_terms = understanding.focus_terms[:4]
        if not focus_terms:
            return suggestions
        existing_topics = {
            entry.topic.lower() for entry in memory.recall("synthetic::")[-100:]
        }
        for trace in traces[:6]:
            if len(suggestions) >= self._max_harvest_queries:
                break
            focus = trace.focus.lower().replace(" ", "-")
            topic_key = f"synthetic::{focus}"
            if topic_key in existing_topics:
                continue
            query = f"{trace.focus} {trace.module} procedural patterns"
            if query not in suggestions:
                suggestions.append(query)
        return suggestions

    def _style_hint(
        self,
        traces: Sequence[ModuleTrace],
        understanding: MessageUnderstanding,
    ) -> str:
        if understanding.affect == "positive":
            return "uplifting conversational cadence"
        if understanding.urgency:
            return "succinct decision-first framing"
        if any(trace.category == "Third Wave" for trace in traces[:3]):
            return "imaginative but verifiable narration"
        if any(trace.category == "Second Wave" for trace in traces[:3]):
            return "structured abstraction with grounded metaphors"
        return "evidence-led explanation"


# ---------------------------------------------------------------------------
# Blueprint builders
# ---------------------------------------------------------------------------


def _build_modules() -> List[ProceduralModule]:
    modules: List[ProceduralModule] = []
    for name, mechanism, description, keywords, weight, category in _MODULE_BLUEPRINTS:
        modules.append(
            ProceduralModule(
                name=name,
                category=category,
                mechanism=mechanism,
                description=description,
                keywords=tuple(keywords),
                base_weight=weight,
            )
        )
    return modules


def _build_knowledge_fields() -> Tuple[ProceduralKnowledgeField, ...]:
    return (
        ProceduralKnowledgeField(
            domain="grammar",
            generator="Fractal grammar reconstruction",
            descriptors=("expanding clauses", "mirroring tone", "evolving registers"),
        ),
        ProceduralKnowledgeField(
            domain="conversation",
            generator="Dialogue resonance modelling",
            descriptors=("tracking affect", "balancing initiative", "closing loops"),
        ),
        ProceduralKnowledgeField(
            domain="coding",
            generator="Symbolic algorithm rehearsal",
            descriptors=("building invariants", "profiling performance", "running regression suites"),
        ),
    )


# ---------------------------------------------------------------------------
# Static datasets (compressed generators rather than literal thousands)
# ---------------------------------------------------------------------------

_GRAMMAR_TOPICS: Tuple[str, ...] = (
    "subject verb agreement",
    "modal verbs",
    "conditional clauses",
    "relative clauses",
    "participial phrases",
    "comparative structures",
    "superlative structures",
    "parallel construction",
    "discourse markers",
    "rhetorical questions",
    "cause and effect chains",
    "contrastive connectors",
    "analogy builders",
    "definition frames",
    "stepwise procedures",
    "counterargument framing",
    "narrative pacing",
    "technical summaries",
    "evidence integration",
    "citation cadence",
    "tone modulation",
    "register switching",
    "question scaffolding",
    "teaching sequences",
    "story hooks",
    "metaphor weaving",
    "sensory grounding",
    "reflection prompts",
    "empathy statements",
    "evidence lead-ins",
)

_CONVERSATION_ARCS: Tuple[str, ...] = (
    "greet clarify respond",
    "acknowledge probe align",
    "teach demonstrate recap",
    "coach challenge encourage",
    "question analyse resolve",
    "listen validate propose",
    "diagnose hypothesize test",
    "mirror empathise redirect",
    "summarise check invite",
    "celebrate reinforce plan",
    "calm stabilise decide",
    "brainstorm filter prioritise",
    "debate weigh conclude",
    "reflect adapt iterate",
    "mentor scaffold empower",
    "co-create imagine refine",
)

_CODING_MOVES: Tuple[str, ...] = (
    "design data model",
    "refactor module",
    "stabilise API",
    "optimise loop",
    "profile bottleneck",
    "debug state",
    "secure endpoint",
    "balance load",
    "orchestrate service",
    "harden tests",
    "document contract",
    "migrate dependency",
    "sandbox experiment",
    "simulate economy",
    "monitor telemetry",
    "enforce lint",
    "compose patterns",
    "tune memory",
    "evaluate algorithm",
    "validate schema",
)

_MODULE_BLUEPRINTS: Tuple[Tuple[str, str, str, Tuple[str, ...], float, str], ...] = (
    (
        "Symbolic AI Revival",
        "assemble logic trees and deterministic grammars",
        "Revives explicit rule-based reasoning with full traceability.",
        ("logic", "grammar", "rule", "symbolic"),
        0.64,
        "Foundational",
    ),
    (
        "Retrieval + Composition AI",
        "retrieve verified fragments and compose fresh narratives",
        "Acts like an elite librarian stitching evidence into coherent answers.",
        ("retrieve", "compose", "evidence", "library"),
        0.66,
        "Foundational",
    ),
    (
        "Algorithmic Transformer Emulator",
        "build transient attention maps with procedural weights",
        "Emulates transformer flows using on-the-fly attention structures.",
        ("attention", "map", "sequence", "transformer"),
        0.62,
        "Foundational",
    ),
    (
        "Procedural Concept Engine",
        "run miniature simulations and logic procedures",
        "Learns by executing procedural experiments instead of memorising text.",
        ("simulate", "procedure", "concept", "experiment"),
        0.63,
        "Foundational",
    ),
    (
        "Swarm-Based Intelligence",
        "orchestrate micro-agents to debate and vote",
        "Hundreds of lightweight actors converge toward consensus answers.",
        ("swarm", "agent", "vote", "debate"),
        0.6,
        "Foundational",
    ),
    (
        "Compression AI",
        "treat reasoning as compression and decompression",
        "Chooses statements that yield maximal information density.",
        ("compress", "entropy", "ratio", "information"),
        0.61,
        "Foundational",
    ),
    (
        "Fractal Language Engine",
        "expand grammar rules recursively as context grows",
        "Language evolves fractally, adapting registers in real-time.",
        ("fractal", "grammar", "recursive", "evolve"),
        0.67,
        "Second Wave",
    ),
    (
        "Algorithmic Dreaming System",
        "generate speculative ideas via controlled noise",
        "Produces creative hypotheses that are later verified in the forge.",
        ("dream", "noise", "idea", "speculative"),
        0.58,
        "Second Wave",
    ),
    (
        "Constraint-Based Language Solver",
        "solve sentences as logic puzzles",
        "Ensures outputs satisfy grammatical and semantic constraints.",
        ("constraint", "solver", "puzzle", "logic"),
        0.6,
        "Second Wave",
    ),
    (
        "Physics-Inspired AI",
        "model meanings as forces reaching equilibrium",
        "Balances attractive and repulsive conceptual forces.",
        ("force", "equilibrium", "physics", "balance"),
        0.59,
        "Second Wave",
    ),
    (
        "Cognitive Map Emulator",
        "navigate semantic landscapes like a GPS",
        "Finds optimal knowledge paths between ideas.",
        ("map", "navigate", "path", "landscape"),
        0.6,
        "Second Wave",
    ),
    (
        "Evolutionary Text Synthesizer",
        "mutate and select candidate sentences",
        "Iteratively evolves phrasing until coherence emerges.",
        ("evolve", "mutation", "fitness", "sentence"),
        0.6,
        "Second Wave",
    ),
    (
        "Quantum-Logic Simulator",
        "collapse semantic superpositions based on context",
        "Handles ambiguity like quantum states collapsing to precise answers.",
        ("quantum", "superposition", "collapse", "context"),
        0.57,
        "Second Wave",
    ),
    (
        "Contextual Compression Oracle",
        "rank candidate responses by compression ratio",
        "Selects phrasing that maximises insight per token.",
        ("compression", "ratio", "oracle", "concise"),
        0.61,
        "Second Wave",
    ),
    (
        "Procedural Brain Emulator",
        "route tasks across logic, emotion, memory, language lobes",
        "Mirrors cortical specialisation with modular routines.",
        ("lobe", "cortex", "memory", "language"),
        0.62,
        "Second Wave",
    ),
    (
        "Interactive Thought Web",
        "build navigable graphs of connected concepts",
        "Lets users traverse reasoning nodes interactively.",
        ("graph", "interactive", "concept", "web"),
        0.6,
        "Second Wave",
    ),
    (
        "Cultural Mimic Engine",
        "remix archetypes and narrative tropes",
        "Blends cultural references responsibly to enrich explanations.",
        ("culture", "trope", "archetype", "story"),
        0.59,
        "Third Wave",
    ),
    (
        "Linguistic Resonance Field",
        "tune words to semantic frequencies",
        "Matches tone by aligning resonance patterns in vocabulary.",
        ("resonance", "frequency", "tone", "vibrate"),
        0.6,
        "Third Wave",
    ),
    (
        "Cognitive Cellular Automaton",
        "grow sentences from local interaction rules",
        "Complex narratives emerge from simple local updates.",
        ("cellular", "automaton", "pattern", "emerge"),
        0.58,
        "Third Wave",
    ),
    (
        "Dream Cache System",
        "reuse and mutate prior outputs",
        "Builds long-term identity by refining previous conversations.",
        ("dream", "cache", "mutate", "reuse"),
        0.6,
        "Third Wave",
    ),
    (
        "Dynamic Ontology Weaver",
        "expand live concept webs while conversing",
        "Keeps ontology fresh by integrating new relationships.",
        ("ontology", "weave", "relationship", "graph"),
        0.6,
        "Third Wave",
    ),
    (
        "Paradox Engine",
        "surface contradictions and reconcile them",
        "Leverages pro/con debate to reach nuanced conclusions.",
        ("paradox", "debate", "pro", "con"),
        0.59,
        "Third Wave",
    ),
    (
        "Information Thermodynamics AI",
        "treat reasoning as entropy minimisation",
        "Optimises statements for maximal certainty gains.",
        ("entropy", "temperature", "energy", "certainty"),
        0.58,
        "Third Wave",
    ),
    (
        "Meta-Rewriter Core",
        "transform drafts instead of generating from scratch",
        "Iteratively rewrites until clarity and intent align.",
        ("rewrite", "draft", "revise", "clarity"),
        0.61,
        "Third Wave",
    ),
    (
        "Semantic Circuit Board",
        "propagate signals across concept nodes",
        "Reasoning becomes electrical flow through conceptual circuits.",
        ("circuit", "node", "signal", "propagate"),
        0.6,
        "Third Wave",
    ),
    (
        "Compression Feedback Oracle",
        "rewrite answers until compression is optimal",
        "Enforces an edit loop that balances brevity and depth.",
        ("feedback", "compress", "rewrite", "optimize"),
        0.6,
        "Third Wave",
    ),
    (
        "Algorithmic Consciousness Emulator",
        "coordinate attention, emotion, reflection modules",
        "Maintains a shared awareness buffer for submodules.",
        ("awareness", "buffer", "emotion", "attention"),
        0.62,
        "Third Wave",
    ),
    (
        "Neural Mirage",
        "generate pseudo-weights procedurally",
        "Simulates deep learning patterns without storing massive matrices.",
        ("pseudo", "weight", "hash", "simulate"),
        0.6,
        "Third Wave",
    ),
    (
        "Fractal Debate Society",
        "run recursive internal debates",
        "Mini thinkers argue until consensus forms.",
        ("debate", "recursive", "society", "consensus"),
        0.61,
        "Third Wave",
    ),
    (
        "Cognitive Hologram",
        "store knowledge in overlapping interference patterns",
        "Every fragment can reconstruct the whole idea.",
        ("hologram", "interference", "overlap", "reconstruct"),
        0.59,
        "Third Wave",
    ),
    (
        "Entropy-Guided Creativity Engine",
        "inject controlled randomness",
        "Generates near-chaotic originality while respecting constraints.",
        ("creativity", "random", "entropy", "novel"),
        0.58,
        "Third Wave",
    ),
    (
        "Reflexive Meta-Loop",
        "continuously reread and improve outputs",
        "Polishes phrasing until no further gain is detected.",
        ("reflexive", "loop", "improve", "iterate"),
        0.6,
        "Third Wave",
    ),
    (
        "Procedural Knowledge Fields",
        "generate deterministic meaning vectors",
        "Uses fractals and symbolic expansions to rebuild knowledge on demand.",
        ("procedural", "field", "vector", "meaning"),
        0.65,
        "Lightweight",
    ),
)

_SYNTHETIC_DOMAINS: Tuple[Tuple[str, str, str], ...] = (
    ("https://synthetic.eidolon.prime/docs", "A", "Synthetic docs and standards"),
    ("https://synthetic.eidolon.prime/tutorials", "B", "Applied tutorials curated nightly"),
    ("https://synthetic.eidolon.prime/conversations", "C", "Tone exemplars and rhetorical moves"),
    ("https://synthetic.eidolon.prime/experiments", "S", "Self-experiments verified in the forge"),
)

_SYNTHETIC_TOPIC_ROOTS: Tuple[str, ...] = (
    "roblox economy",
    "grammar mastery",
    "lua optimisation",
    "ethics in automation",
    "conversation tone",
    "evidence synthesis",
    "player psychology",
    "systems balancing",
    "curriculum design",
    "testing discipline",
    "accessibility practice",
    "community health",
    "storytelling craft",
    "algorithm design",
    "security review",
    "data compression",
    "semantic navigation",
    "symbolic reasoning",
    "empathy cues",
    "debate choreography",
    "metaphor building",
    "physics metaphors",
    "creative dreaming",
    "procedural knowledge",
)

_SYNTHETIC_TOPIC_FACETS: Tuple[str, ...] = (
    "blueprints",
    "trusted sources",
    "case studies",
    "playbooks",
    "exercises",
    "refresh notes",
)


def _build_topic_clusters() -> Tuple[str, ...]:
    clusters: set[str] = set()
    for domain in _SYNTHETIC_TOPIC_ROOTS:
        for facet in _SYNTHETIC_TOPIC_FACETS:
            base = f"{domain} {facet}"
            clusters.add(base)
            for segment in range(1, 21):
                clusters.add(f"{base} segment-{segment:02d}")
    return tuple(sorted(clusters))


_SYNTHETIC_TOPIC_CLUSTERS: Tuple[str, ...] = _build_topic_clusters()
