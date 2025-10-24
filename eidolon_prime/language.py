"""Grammar datastore and language realization utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

_ROBLOX_SNIPPETS: Dict[str, str] = {
    "quest": "\n".join(
        [
            "```lua",
            "local QuestOrchestrator = {}",
            "",
            "local ServerStorage = game:GetService(\"ServerStorage\")",
            "local MessagingService = game:GetService(\"MessagingService\")",
            "",
            "function QuestOrchestrator.publishQuest(definition)",
            "    assert(definition.id, \"Quest definition requires an id\")",
            "    definition.cooldown = definition.cooldown or 120",
            "    definition.reward = definition.reward or {currency = \"Coins\", amount = 50}",
            "    MessagingService:PublishAsync(\"quests:new\", definition)",
            "end",
            "",
            "return QuestOrchestrator",
            "```",
        ]
    ),
    "economy": "\n".join(
        [
            "```lua",
            "local EconomyBalancer = {}",
            "",
            "local MarketplaceService = game:GetService(\"MarketplaceService\")",
            "",
            "local state = {",
            "    velocity = 1.0,",
            "    targetVelocity = 1.35,",
            "    smoothing = 0.12,",
            "}",
            "",
            "function EconomyBalancer.trackPurchase(player, productId, amount)",
            "    if state.velocity > 1.5 then",
            "        MarketplaceService:PerformPurchase(player, productId, amount * 0.85)",
            "    else",
            "        MarketplaceService:PerformPurchase(player, productId, amount)",
            "    end",
            "end",
            "",
            "return EconomyBalancer",
            "```",
        ]
    ),
    "telemetry": "\n".join(
        [
            "```lua",
            "local SessionInsights = {}",
            "",
            "local HttpService = game:GetService(\"HttpService\")",
            "",
            "local ENDPOINT = \"https://telemetry.example.com/events\"",
            "",
            "function SessionInsights.emit(eventName, payload)",
            "    payload.timestamp = os.time()",
            "    payload.event = eventName",
            "    HttpService:PostAsync(ENDPOINT, HttpService:JSONEncode(payload))",
            "end",
            "",
            "return SessionInsights",
            "```",
        ]
    ),
}


@dataclass
class SemanticFrame:
    """Meaning representation produced before surface realization."""

    intent: str
    topic: str
    user_message: str
    key_points: List[str]
    evidence: List[str]
    actions: List[str]
    emotional_tone: str
    call_to_action: str
    outcome: str

    def condensed_topic(self) -> str:
        if not self.topic:
            return "the subject you raised"
        cleaned = self.topic.replace("_", " ").strip()
        return cleaned or "the subject you raised"


@dataclass
class GrammarTemplate:
    """Reusable rhetorical structure used to craft sentences."""

    template_id: str
    rhetorical_function: str
    slots: Dict[str, str]
    register_tags: Sequence[str]
    variation_ops: Sequence[str] = field(default_factory=tuple)


@dataclass
class RegisterPack:
    """Defines vocabulary and tone for a writing register."""

    name: str
    openers: Sequence[str]
    connectors: Sequence[str]
    closings: Sequence[str]
    hedges: Sequence[str]

    def pick(self, items: Sequence[str], variant: int) -> str:
        if not items:
            return ""
        index = variant % len(items)
        return items[index]

    def opener(self, variant: int) -> str:
        return self.pick(self.openers, variant)

    def connector(self, variant: int) -> str:
        return self.pick(self.connectors, variant)

    def closing(self, variant: int) -> str:
        return self.pick(self.closings, variant)

    def hedge(self, variant: int) -> str:
        return self.pick(self.hedges, variant)


_DEFAULT_TEMPLATES: Tuple[GrammarTemplate, ...] = (
    GrammarTemplate(
        template_id="explain_sequence",
        rhetorical_function="explain",
        slots={
            "introduction": "{opener} {topic_sentence} {tone_clause}",
            "analysis": "{connector} {analysis_sentence}",
            "evidence": "{connector} {evidence_sentence}",
            "action": "{connector} {action_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("technical_conversational", "balanced"),
        variation_ops=("shuffle_support", "cause_effect"),
    ),
    GrammarTemplate(
        template_id="diagnose_strategy",
        rhetorical_function="problem_solving",
        slots={
            "introduction": "{opener} {topic_sentence} {tone_clause}",
            "analysis": "{connector} {diagnosis_sentence}",
            "action": "{connector} {strategy_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("analytical",),
        variation_ops=("highlight_decision",),
    ),
    GrammarTemplate(
        template_id="clarify_answer_invite",
        rhetorical_function="question",
        slots={
            "introduction": "{opener} {clarify_sentence}",
            "analysis": "{connector} {answer_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("technical_conversational", "balanced"),
        variation_ops=("invite_followup",),
    ),
    GrammarTemplate(
        template_id="story_lesson",
        rhetorical_function="motivate",
        slots={
            "introduction": "{opener} {story_hook}",
            "analysis": "{connector} {lesson_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("narrative", "balanced"),
        variation_ops=("amplify_emotion",),
    ),
    GrammarTemplate(
        template_id="acknowledge_analyse",
        rhetorical_function="universal",
        slots={
            "introduction": "{opener} {ack_sentence}",
            "analysis": "{connector} {analysis_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("balanced",),
        variation_ops=("cause_effect",),
    ),
    GrammarTemplate(
        template_id="analysis_compare_decide",
        rhetorical_function="analysis",
        slots={
            "introduction": "{opener} {topic_sentence} {tone_clause}",
            "analysis": "{connector} {analysis_sentence}",
            "comparison": "{connector} {comparison_sentence}",
            "decision": "{connector} {decision_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("analytical", "technical_conversational"),
        variation_ops=("cause_effect", "highlight_decision"),
    ),
    GrammarTemplate(
        template_id="code_review_sequence",
        rhetorical_function="coding",
        slots={
            "introduction": "{opener} {topic_sentence} {tone_clause}",
            "analysis": "{connector} {code_reasoning_sentence}",
            "evidence": "{connector} {coding_evidence_sentence}",
            "action": "{connector} {coding_action_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("engineering", "technical_conversational"),
        variation_ops=("code_focus", "precision_pass"),
    ),
    GrammarTemplate(
        template_id="dialogue_loop",
        rhetorical_function="conversation",
        slots={
            "introduction": "{opener} {clarify_sentence}",
            "analysis": "{connector} {analysis_sentence}",
            "reflection": "{connector} {reflection_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("dialogue_support", "balanced"),
        variation_ops=("invite_followup", "shuffle_support"),
    ),
    GrammarTemplate(
        template_id="essay_argument",
        rhetorical_function="essay",
        slots={
            "introduction": "{opener} {thesis_hook}",
            "thesis": "{thesis_sentence}",
            "support": "{support_sentence}",
            "contrast": "{contrast_sentence}",
            "synthesis": "{synthesis_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("essay_formal",),
        variation_ops=("cause_effect", "highlight_decision"),
    ),
    GrammarTemplate(
        template_id="creative_arc",
        rhetorical_function="creative",
        slots={
            "introduction": "{opener} {creative_hook_sentence}",
            "hook": "{creative_hook_detail}",
            "development": "{connector} {creative_development_sentence}",
            "turn": "{connector} {creative_turn_sentence}",
            "resolution": "{connector} {creative_resolution_sentence}",
            "reflection": "{creative_reflection_sentence}",
        },
        register_tags=("creative_narrative",),
        variation_ops=("amplify_emotion",),
    ),
    GrammarTemplate(
        template_id="news_briefing",
        rhetorical_function="current_events",
        slots={
            "introduction": "{opener} {world_context_sentence}",
            "situation": "{world_situation_sentence}",
            "evidence": "{world_evidence_sentence}",
            "implication": "{world_implication_sentence}",
            "outlook": "{world_outlook_sentence}",
            "closing": "{closing_sentence}",
        },
        register_tags=("current_affairs",),
        variation_ops=("cause_effect",),
    ),
)


_DEFAULT_REGISTERS: Tuple[RegisterPack, ...] = (
    RegisterPack(
        name="technical_conversational",
        openers=(
            "Thanks for raising this.",
            "Great question to explore.",
            "Let's unpack this together.",
        ),
        connectors=("From training I learned that", "Drawing on recent lessons,", "In practice,"),
        closings=(
            "Happy to adapt the plan if you want to go deeper.",
            "Let me know if you want a follow-up drill.",
            "I'm ready to iterate with you on this.",
        ),
        hedges=("typically", "usually", "often"),
    ),
    RegisterPack(
        name="analytical",
        openers=("Here is what the diagnostics show.", "Let's map the moving parts."),
        connectors=("First,", "Meanwhile,", "To steer this,"),
        closings=(
            "We can review metrics together after the next experiment.",
            "I'll keep monitoring the signals we highlighted.",
        ),
        hedges=("deliberately", "precisely"),
    ),
    RegisterPack(
        name="narrative",
        openers=("Imagine the path a seasoned creator took.", "Picture a team in the same spot."),
        connectors=("In their case,", "What they discovered was", "It turned when"),
        closings=(
            "Let's channel that momentum in your next move.",
            "You can build a similar arc step by step.",
        ),
        hedges=("honestly", "notably"),
    ),
    RegisterPack(
        name="balanced",
        openers=("I hear what you're aiming for.", "Let's stay grounded."),
        connectors=("Here's how it lines up", "From a systems view", "Consider that"),
        closings=(
            "I'm beside you as we keep refining this.",
            "Share any pushback and we'll re-evaluate together.",
        ),
        hedges=("carefully", "thoughtfully"),
    ),
    RegisterPack(
        name="dialogue_support",
        openers=(
            "Thanks for opening up about this.",
            "Let's sync our understanding first.",
            "I appreciate you sharing the context.",
        ),
        connectors=(
            "As we unpack this,",
            "Here's what I'm hearing,",
            "To keep the dialogue flowing,",
        ),
        closings=(
            "I'm here for more conversation as you think it through.",
            "Feel free to bounce more thoughts back at me.",
            "Let's keep the exchange going whenever you're ready.",
        ),
        hedges=("gently", "openly", "collaboratively"),
    ),
    RegisterPack(
        name="engineering",
        openers=(
            "Let's engineer this carefully.",
            "From an implementation point of view,",
            "Thinking like a systems architect,",
        ),
        connectors=(
            "From an implementation angle,",
            "Code-wise,",
            "To keep the build stable,",
        ),
        closings=(
            "I'll keep refining the implementation notes with you.",
            "Let's validate the code path together when you're ready.",
        ),
        hedges=("technically", "precisely", "code-wise"),
    ),
    RegisterPack(
        name="essay_formal",
        openers=(
            "Let's outline the argument carefully.",
            "Here is the thesis I'm advancing.",
            "I'll develop the case step by step.",
        ),
        connectors=("First,", "Next,", "Furthermore"),
        closings=(
            "That synthesis keeps the essay focused and defensible.",
            "We can expand each paragraph with citations if you need more depth.",
        ),
        hedges=("formally", "precisely"),
    ),
    RegisterPack(
        name="creative_narrative",
        openers=(
            "Let's open in motion.",
            "Picture the first beat vividly.",
            "We'll set the tone immediately.",
        ),
        connectors=(
            "As the scene unfolds,",
            "When the tension spikes,",
            "From the character's view,",
        ),
        closings=(
            "That cadence leaves room for another chapter.",
            "Carry the emotional thread into the next vignette.",
        ),
        hedges=("imaginatively", "boldly"),
    ),
    RegisterPack(
        name="current_affairs",
        openers=(
            "Here's what the latest verified reports show.",
            "I'll brief you on today's landscape.",
            "Let's anchor the update in current data.",
        ),
        connectors=(
            "In parallel,",
            "Data from partners notes",
            "Analysts highlight",
        ),
        closings=(
            "I'll keep monitoring feeds for significant shifts.",
            "Ping me if you need deeper sourcing on any thread.",
        ),
        hedges=("currently", "notably"),
    ),
)


class GrammarDatastore:
    """Provides templates and register packs for the language engine."""

    def __init__(self) -> None:
        self._templates: Dict[str, GrammarTemplate] = {
            template.template_id: template for template in _DEFAULT_TEMPLATES
        }
        self._registers: Dict[str, RegisterPack] = {
            register.name: register for register in _DEFAULT_REGISTERS
        }

    def template_for_structure(self, structure: str) -> GrammarTemplate:
        lookup = {
            "teach→example→recap": "explain_sequence",
            "diagnose→strategy→next-step": "diagnose_strategy",
            "clarify→answer→invite": "clarify_answer_invite",
            "story→insight→encourage": "story_lesson",
            "story→lesson→next-step": "story_lesson",
            "acknowledge→analysis→summary": "acknowledge_analyse",
            "acknowledge→contrast→resolve": "acknowledge_analyse",
            "teach→drill→recap": "explain_sequence",
            "analyze→compare→decide": "analysis_compare_decide",
            "analyse→compare→decide": "analysis_compare_decide",
            "greet→explore→respond→reflect": "dialogue_loop",
            "greet→clarify→respond→reflect": "dialogue_loop",
            "diagnose→code→next-step": "code_review_sequence",
            "teach→code→recap": "code_review_sequence",
            "thesis→support→contrast→synthesis→next-step": "essay_argument",
            "hook→development→turn→resolution→reflection": "creative_arc",
            "situation→evidence→implication→outlook": "news_briefing",
        }
        template_id = lookup.get(structure, "acknowledge_analyse")
        return self._templates[template_id]

    def register_pack(self, name: str) -> RegisterPack:
        return self._registers.get(name, self._registers["balanced"])

    def add_template(self, template: GrammarTemplate) -> None:
        self._templates[template.template_id] = template

    def add_register(self, register: RegisterPack) -> None:
        self._registers[register.name] = register

    def realize(
        self,
        frame: SemanticFrame,
        template: GrammarTemplate,
        register: RegisterPack,
        variant: int = 0,
    ) -> Dict[str, str]:
        """Return populated slot text for a given template and register."""

        context = self._build_context(frame, register, variant)
        sentences: Dict[str, str] = {}
        for slot, pattern in template.slots.items():
            sentences[slot] = pattern.format(**context)
        return sentences

    def _build_context(
        self, frame: SemanticFrame, register: RegisterPack, variant: int
    ) -> Dict[str, str]:
        opener = register.opener(variant)
        connector = register.connector(variant)
        closing = register.closing(variant)
        hedge = register.hedge(variant)
        topic_sentence = (
            f"We're focusing on {frame.condensed_topic()} based on your message."
        )
        analysis_sentence = self._compose_analysis_sentence(frame, hedge)
        evidence_sentence = self._compose_evidence_sentence(frame, hedge)
        action_sentence = self._compose_action_sentence(frame)
        diagnosis_sentence = self._compose_diagnosis_sentence(frame, hedge)
        strategy_sentence = self._compose_strategy_sentence(frame)
        clarify_sentence = self._compose_clarify_sentence(frame, hedge)
        answer_sentence = self._compose_answer_sentence(frame)
        story_hook = self._compose_story_hook(frame)
        lesson_sentence = self._compose_lesson_sentence(frame)
        ack_sentence = self._compose_ack_sentence(frame, hedge)
        comparison_sentence = self._compose_comparison_sentence(frame)
        decision_sentence = self._compose_decision_sentence(frame)
        reflection_sentence = self._compose_reflection_sentence(frame)
        closing_sentence = self._compose_closing_sentence(frame, closing)
        tone_clause = f"I'm keeping the tone {frame.emotional_tone}."
        code_reasoning_sentence = self._compose_code_reasoning_sentence(frame, hedge)
        coding_evidence_sentence = self._compose_coding_evidence_sentence(frame)
        coding_action_sentence = self._compose_coding_action_sentence(frame)
        thesis_hook = self._compose_thesis_hook(frame)
        thesis_sentence = self._compose_thesis_sentence(frame, hedge)
        support_sentence = self._compose_support_sentence(frame)
        contrast_sentence = self._compose_contrast_sentence(frame)
        synthesis_sentence = self._compose_synthesis_sentence(frame)
        creative_hook_sentence = self._compose_creative_hook_sentence(frame)
        creative_hook_detail = self._compose_creative_hook_detail(frame)
        creative_development_sentence = self._compose_creative_development_sentence(frame)
        creative_turn_sentence = self._compose_creative_turn_sentence(frame)
        creative_resolution_sentence = self._compose_creative_resolution_sentence(frame)
        creative_reflection_sentence = self._compose_creative_reflection_sentence(frame, closing)
        world_context_sentence = self._compose_world_context_sentence(frame)
        world_situation_sentence = self._compose_world_situation_sentence(frame)
        world_evidence_sentence = self._compose_world_evidence_sentence(frame)
        world_implication_sentence = self._compose_world_implication_sentence(frame)
        world_outlook_sentence = self._compose_world_outlook_sentence(frame)
        return {
            "opener": opener,
            "connector": connector,
            "closing_sentence": closing_sentence,
            "topic_sentence": topic_sentence,
            "tone_clause": tone_clause,
            "analysis_sentence": analysis_sentence,
            "evidence_sentence": evidence_sentence,
            "action_sentence": action_sentence,
            "diagnosis_sentence": diagnosis_sentence,
            "strategy_sentence": strategy_sentence,
            "clarify_sentence": clarify_sentence,
            "answer_sentence": answer_sentence,
            "story_hook": story_hook,
            "lesson_sentence": lesson_sentence,
            "ack_sentence": ack_sentence,
            "comparison_sentence": comparison_sentence,
            "decision_sentence": decision_sentence,
            "reflection_sentence": reflection_sentence,
            "code_reasoning_sentence": code_reasoning_sentence,
            "coding_evidence_sentence": coding_evidence_sentence,
            "coding_action_sentence": coding_action_sentence,
            "thesis_hook": thesis_hook,
            "thesis_sentence": thesis_sentence,
            "support_sentence": support_sentence,
            "contrast_sentence": contrast_sentence,
            "synthesis_sentence": synthesis_sentence,
            "creative_hook_sentence": creative_hook_sentence,
            "creative_hook_detail": creative_hook_detail,
            "creative_development_sentence": creative_development_sentence,
            "creative_turn_sentence": creative_turn_sentence,
            "creative_resolution_sentence": creative_resolution_sentence,
            "creative_reflection_sentence": creative_reflection_sentence,
            "world_context_sentence": world_context_sentence,
            "world_situation_sentence": world_situation_sentence,
            "world_evidence_sentence": world_evidence_sentence,
            "world_implication_sentence": world_implication_sentence,
            "world_outlook_sentence": world_outlook_sentence,
        }

    def _compose_analysis_sentence(self, frame: SemanticFrame, hedge: str) -> str:
        if frame.key_points:
            primary = self._tidy(frame.key_points[0])
            return f"{hedge.title()} speaking, the key signal is that {primary}."
        return "I'm still distilling the right signal."

    def _compose_evidence_sentence(self, frame: SemanticFrame, hedge: str) -> str:
        if frame.evidence:
            evidence = self._tidy(frame.evidence[0])
            return f"{hedge.title()} I rely on training evidence such as {evidence}."
        return "I'm ready to gather more evidence as needed."

    def _compose_action_sentence(self, frame: SemanticFrame) -> str:
        if frame.actions:
            return f"Next, I recommend {self._tidy(frame.actions[0])}."
        return "We can collect more data before committing to a move."

    def _compose_code_reasoning_sentence(
        self, frame: SemanticFrame, hedge: str
    ) -> str:
        prefix = f"{hedge.title()} " if hedge else "Technically, "
        if frame.key_points:
            anchor = self._tidy(frame.key_points[0])
            return f"{prefix}from a coding perspective the logic centres on {anchor}."
        return (
            f"{prefix}from a coding perspective I decompose the idea into reusable functions "
            "before writing syntax."
        )

    def _compose_coding_evidence_sentence(self, frame: SemanticFrame) -> str:
        if frame.evidence:
            proof = self._tidy(frame.evidence[0])
            return f"Implementation references include {proof}."
        return "I'll cross-check trusted repositories and specifications to anchor the implementation."

    def _compose_coding_action_sentence(self, frame: SemanticFrame) -> str:
        snippet = self._extract_code_snippet(frame.evidence)
        if snippet:
            return (
                "I'll translate that into code by stitching this Luau blueprint:\n"
                + snippet
            )
        message_text = frame.user_message.lower()
        if "roblox" in message_text and "script" in message_text:
            for keyword, code in _ROBLOX_SNIPPETS.items():
                if keyword in message_text:
                    return (
                        "I'll translate that into code by stitching this Luau blueprint:\n"
                        + code
                    )
            return (
                "I'll translate that into code by stitching this Luau blueprint:\n"
                + _ROBLOX_SNIPPETS["quest"]
            )
        if frame.actions:
            step = self._tidy(frame.actions[0])
            return f"I'll translate that into code by {step}."
        return "I'll sketch function signatures and test cases so the code path is well reasoned."

    def _compose_thesis_hook(self, frame: SemanticFrame) -> str:
        topic = frame.condensed_topic()
        return f"We're developing an argument that orbits {topic}."

    def _compose_thesis_sentence(self, frame: SemanticFrame, hedge: str) -> str:
        if frame.key_points:
            thesis = self._tidy(frame.key_points[0])
            prefix = f"{hedge.capitalize()} " if hedge else "Formally, "
            return f"{prefix}the thesis is that {thesis}."
        return "Formally, the thesis is that thoughtful design choices uphold player trust."

    def _compose_support_sentence(self, frame: SemanticFrame) -> str:
        if frame.evidence:
            support = self._tidy(frame.evidence[0])
            return f"We support it with evidence like {support}."
        return "We support it with curated creative-writing drills and verified Roblox playbooks."

    def _compose_contrast_sentence(self, frame: SemanticFrame) -> str:
        if len(frame.key_points) > 1:
            contrast = self._tidy(frame.key_points[1])
            return f"A counter-weight considers {contrast}."
        if frame.evidence and len(frame.evidence) > 1:
            return f"A contrasting signal notes {self._tidy(frame.evidence[1])}."
        return "We acknowledge opposing pressures such as scope creep or pacing fatigue."

    def _compose_synthesis_sentence(self, frame: SemanticFrame) -> str:
        if frame.actions:
            synthesis = self._tidy(frame.actions[0])
            return f"The synthesis is to {synthesis}."
        if frame.outcome:
            return f"The synthesis is to honour the outcome: {self._tidy(frame.outcome)}."
        return "The synthesis is to test ideas in stages and cite results transparently."

    def _compose_creative_hook_sentence(self, frame: SemanticFrame) -> str:
        topic = frame.condensed_topic()
        return f"We drop into {topic} with a sensory-rich opening beat."

    def _compose_creative_hook_detail(self, frame: SemanticFrame) -> str:
        if frame.key_points:
            detail = self._tidy(frame.key_points[0])
            return f"The first paragraph anchors on {detail}."
        return "The first paragraph sketches the protagonist's immediate stakes."

    def _compose_creative_development_sentence(self, frame: SemanticFrame) -> str:
        if frame.evidence:
            development = self._tidy(frame.evidence[0])
            return f"As the scene builds, weave in {development}."
        return "As the scene builds, interleave dialogue with textural detail to keep momentum."

    def _compose_creative_turn_sentence(self, frame: SemanticFrame) -> str:
        if len(frame.key_points) > 1:
            turn = self._tidy(frame.key_points[1])
            return f"When tension peaks, pivot through {turn}."
        return "When tension peaks, pivot through an unexpected choice that still honours prior foreshadowing."

    def _compose_creative_resolution_sentence(self, frame: SemanticFrame) -> str:
        if frame.actions:
            action = self._tidy(frame.actions[0])
            return f"Resolve the beat by {action}."
        return "Resolve the beat by rewarding the character's growth without closing future doors."

    def _compose_creative_reflection_sentence(
        self, frame: SemanticFrame, closing: str
    ) -> str:
        if frame.outcome:
            reflection = self._tidy(frame.outcome)
            return f"{reflection} {closing}".strip()
        return closing

    def _compose_world_context_sentence(self, frame: SemanticFrame) -> str:
        topic = frame.condensed_topic()
        return f"Current feeds highlight {topic}."

    def _compose_world_situation_sentence(self, frame: SemanticFrame) -> str:
        if frame.key_points:
            situation = self._tidy(frame.key_points[0])
            return f"Situation: {situation}."
        return "Situation: verified sources summarise the headline trend."

    def _compose_world_evidence_sentence(self, frame: SemanticFrame) -> str:
        if frame.evidence:
            evidence = self._tidy(frame.evidence[0])
            return f"Evidence: {evidence}."
        return "Evidence: I cite timestamped entries from the current events datastore."

    def _compose_world_implication_sentence(self, frame: SemanticFrame) -> str:
        if len(frame.key_points) > 1:
            implication = self._tidy(frame.key_points[1])
            return f"Implication: {implication}."
        if frame.actions:
            return f"Implication: we can {self._tidy(frame.actions[0])}."
        return "Implication: expect downstream changes in community planning and platform policy."

    def _compose_world_outlook_sentence(self, frame: SemanticFrame) -> str:
        if frame.actions and len(frame.actions) > 1:
            return f"Outlook: next we {self._tidy(frame.actions[1])}."
        if frame.outcome:
            return f"Outlook: {self._tidy(frame.outcome)}."
        return "Outlook: I'll continue refreshing the world model as new reports land."

    def _compose_diagnosis_sentence(
        self, frame: SemanticFrame, hedge: str
    ) -> str:
        if len(frame.key_points) > 1:
            secondary = self._tidy(frame.key_points[1])
            return f"{hedge.title()} the constraints revolve around {secondary}."
        return "The main constraint is still emerging."

    def _compose_strategy_sentence(self, frame: SemanticFrame) -> str:
        if frame.actions:
            strategy = self._tidy(frame.actions[0])
            return f"A resilient strategy is to {strategy}."
        return "We can design experiments before picking a strategy."

    def _compose_clarify_sentence(self, frame: SemanticFrame, hedge: str) -> str:
        return (
            f"{hedge.title()} I interpret your intent as exploring {frame.condensed_topic()}"
            f" so I checked which training memories line up."
        )

    def _compose_answer_sentence(self, frame: SemanticFrame) -> str:
        if frame.key_points:
            insight = self._tidy(frame.key_points[0])
            return f"The guidance points toward {insight}."
        return "My training suggests we should gather a bit more detail."

    def _compose_story_hook(self, frame: SemanticFrame) -> str:
        if frame.key_points:
            return f"Someone tackled {frame.condensed_topic()} and noticed {self._tidy(frame.key_points[0])}."
        return f"There's a familiar arc when working with {frame.condensed_topic()}."

    def _compose_lesson_sentence(self, frame: SemanticFrame) -> str:
        if frame.actions:
            return f"Their breakthrough came from {self._tidy(frame.actions[0])}."
        return "Progress arrived once they kept iterating on small experiments."

    def _compose_ack_sentence(self, frame: SemanticFrame, hedge: str) -> str:
        topic = frame.condensed_topic()
        return f"{hedge.title()} I want to acknowledge how important {topic} is to you before we dive deeper."

    def _compose_comparison_sentence(self, frame: SemanticFrame) -> str:
        if len(frame.evidence) > 1:
            primary = self._tidy(frame.evidence[0])
            secondary = self._tidy(frame.evidence[1])
            return f"Comparing signals shows {primary} outweighs {secondary}."
        return "I'm ready to compare alternatives once more evidence arrives."

    def _compose_decision_sentence(self, frame: SemanticFrame) -> str:
        if frame.actions:
            action = self._tidy(frame.actions[0])
            anchor = frame.outcome or frame.condensed_topic()
            return f"Given that, choosing to {action} keeps momentum pointed at {anchor}."
        return "I'll hold off on a recommendation until we map the viable paths."

    def _compose_reflection_sentence(self, frame: SemanticFrame) -> str:
        anchor = frame.outcome or frame.condensed_topic()
        return f"I'm reflecting on how this supports {anchor} so our dialogue stays meaningful."

    def _compose_closing_sentence(
        self, frame: SemanticFrame, closing: str
    ) -> str:
        if frame.call_to_action:
            return f"{frame.call_to_action} {closing}"
        return closing

    def _tidy(self, text: str) -> str:
        cleaned = text.strip()
        while cleaned and cleaned[-1] in ".!?":
            cleaned = cleaned[:-1]
        return cleaned

    def _extract_code_snippet(self, evidence_lines: Sequence[str]) -> str | None:
        for line in evidence_lines:
            _, _, remainder = line.partition("→")
            snippet = remainder.strip() if remainder else line.strip()
            if "(confidence" in snippet:
                snippet = snippet.rsplit("(confidence", 1)[0].strip()
            if "```" in snippet:
                start = snippet.find("```")
                code = snippet[start:]
                if not code.strip():
                    continue
                return code
            if "game:GetService" in snippet:
                body = snippet
                if "```lua" not in body:
                    body = "```lua\n" + body + "\n```"
                return body
        return None

class LanguageEngine:
    """Transforms semantic frames into conversational replies."""

    def __init__(self, datastore: GrammarDatastore) -> None:
        self._datastore = datastore

    def compose_reply(
        self,
        frame: SemanticFrame,
        structure: str,
        register_name: str,
        personality_snapshot: str,
    ) -> Tuple[str, float]:
        template = self._datastore.template_for_structure(structure)
        register = self._datastore.register_pack(register_name)
        candidates: List[Tuple[float, str]] = []
        for variant in range(3):
            slots = self._datastore.realize(frame, template, register, variant)
            slots = self._apply_variations(slots, template.variation_ops, variant)
            paragraphs = self._structure_paragraphs(slots, structure, personality_snapshot)
            candidate = "\n\n".join(paragraphs)
            score = self._score_candidate(candidate)
            candidates.append((score, candidate))
        best_score, best_text = max(candidates, key=lambda item: item[0])
        lowered_message = frame.user_message.lower()
        if "roblox" in lowered_message and "script" in lowered_message:
            for keyword, code in _ROBLOX_SNIPPETS.items():
                if keyword in lowered_message:
                    best_text += "\n\n" + code
                    break
            else:
                best_text += "\n\n" + _ROBLOX_SNIPPETS["quest"]
        lexical = self._lexical_variety(best_text)
        return best_text, lexical

    def _apply_variations(
        self, slots: Dict[str, str], operations: Sequence[str], variant: int
    ) -> Dict[str, str]:
        updated = dict(slots)
        for operation in operations:
            if operation == "shuffle_support":
                updated = self._op_shuffle_support(updated, variant)
            elif operation == "cause_effect":
                updated = self._op_cause_effect(updated)
            elif operation == "highlight_decision":
                updated = self._op_highlight_decision(updated)
            elif operation == "invite_followup":
                updated = self._op_invite_followup(updated)
            elif operation == "amplify_emotion":
                updated = self._op_amplify_emotion(updated)
            elif operation == "code_focus":
                updated = self._op_code_focus(updated)
            elif operation == "precision_pass":
                updated = self._op_precision_pass(updated)
        return updated

    def _structure_paragraphs(
        self, slots: Dict[str, str], structure: str, personality_snapshot: str
    ) -> List[str]:
        structure_parts = structure.split("→")
        paragraphs: List[str] = []
        intro = [slots.get("introduction", "")]
        intro_text = " ".join(part for part in intro if part).strip()
        if intro_text:
            paragraphs.append(intro_text)
        essay_segments = {"thesis", "support", "contrast", "synthesis"}
        creative_segments = {"hook", "development", "turn", "resolution", "reflection"}
        news_segments = {"situation", "evidence", "implication", "outlook"}
        if essay_segments.intersection(structure_parts):
            for key in ("thesis", "support", "contrast", "synthesis"):
                sentence = slots.get(key)
                if sentence:
                    paragraphs.append(sentence)
            if slots.get("closing"):
                paragraphs.append(slots["closing"])
            return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
        if creative_segments.intersection(structure_parts):
            for key in ("hook", "development", "turn", "resolution", "reflection"):
                sentence = slots.get(key)
                if sentence:
                    paragraphs.append(sentence)
            return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
        if news_segments.intersection(structure_parts):
            for key in ("situation", "evidence", "implication", "outlook"):
                sentence = slots.get(key)
                if sentence:
                    paragraphs.append(sentence)
            if slots.get("closing"):
                paragraphs.append(slots["closing"])
            return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
        body_sentences: List[str] = []
        for segment in structure_parts:
            key = self._segment_to_slot(segment)
            if key and slots.get(key):
                if key in {"closing", "introduction"}:
                    continue
                body_sentences.append(slots[key])
        if slots.get("evidence") and slots["evidence"] not in body_sentences:
            body_sentences.append(slots["evidence"])
        if body_sentences:
            paragraphs.append(" ".join(body_sentences))
        if slots.get("closing"):
            paragraphs.append(slots["closing"])
        return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]

    def _segment_to_slot(self, segment: str) -> str:
        mapping = {
            "teach": "analysis",
            "example": "evidence",
            "recap": "closing",
            "diagnose": "analysis",
            "strategy": "action",
            "next-step": "closing",
            "clarify": "introduction",
            "answer": "analysis",
            "invite": "closing",
            "story": "analysis",
            "insight": "analysis",
            "encourage": "closing",
            "acknowledge": "introduction",
            "analysis": "analysis",
            "summary": "closing",
            "lesson": "analysis",
            "contrast": "contrast",
            "compare": "comparison",
            "decide": "decision",
            "decision": "decision",
            "reflect": "reflection",
            "explore": "analysis",
            "respond": "analysis",
            "greet": "introduction",
            "code": "analysis",
            "thesis": "thesis",
            "support": "support",
            "synthesis": "synthesis",
            "hook": "hook",
            "development": "development",
            "turn": "turn",
            "resolution": "resolution",
            "reflection": "reflection",
            "situation": "situation",
            "implication": "implication",
            "outlook": "outlook",
        }
        return mapping.get(segment, "analysis")

    def _op_shuffle_support(self, slots: Dict[str, str], variant: int) -> Dict[str, str]:
        if variant % 2 == 0:
            return slots
        swapped = dict(slots)
        swapped["analysis"], swapped["evidence"] = (
            swapped.get("evidence", swapped.get("analysis", "")),
            swapped.get("analysis", swapped.get("evidence", "")),
        )
        return swapped

    def _op_cause_effect(self, slots: Dict[str, str]) -> Dict[str, str]:
        updated = dict(slots)
        if "analysis" in updated and updated["analysis"]:
            updated["analysis"] += " The supporting evidence right after this line shows why that matters."
        return updated

    def _op_highlight_decision(self, slots: Dict[str, str]) -> Dict[str, str]:
        updated = dict(slots)
        if "action" in updated and updated["action"]:
            updated["action"] += " That keeps the next choice transparent for both of us."
        return updated

    def _op_invite_followup(self, slots: Dict[str, str]) -> Dict[str, str]:
        updated = dict(slots)
        invitation = " If you'd like me to go deeper, just point at a specific angle and I'll expand."
        updated["closing"] = (updated.get("closing", "") + invitation).strip()
        return updated

    def _op_amplify_emotion(self, slots: Dict[str, str]) -> Dict[str, str]:
        updated = dict(slots)
        if "analysis" in updated and updated["analysis"]:
            updated["analysis"] += " I genuinely enjoy helping with topics like this."
        return updated

    def _op_code_focus(self, slots: Dict[str, str]) -> Dict[str, str]:
        updated = dict(slots)
        if "analysis" in updated:
            updated["analysis"] += " I line up pseudo-code so each step is explicit."
        if "evidence" in updated:
            updated["evidence"] += " These references stem from the coding datastore I expanded during atrain."
        return updated

    def _op_precision_pass(self, slots: Dict[str, str]) -> Dict[str, str]:
        updated = dict(slots)
        if "closing" in updated:
            updated["closing"] += " I'll circle back to re-verify terminology and grammar after this exchange."
        return updated

    def _score_candidate(self, text: str) -> float:
        variety = self._lexical_variety(text)
        length_penalty = 0.0
        total_words = len(text.split())
        if total_words < 60:
            length_penalty = -0.05
        elif total_words > 240:
            length_penalty = -0.1
        return 0.7 * variety + 0.3 * (1.0 + length_penalty)

    def _lexical_variety(self, text: str) -> float:
        tokens = [token.strip(".,!?;:").lower() for token in text.split() if token]
        unique = {token for token in tokens if token}
        if not tokens:
            return 0.0
        return len(unique) / len(tokens)
