"""Speech practice academy that teaches Eidolon Prime to converse."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from .language import SemanticFrame, LanguageEngine
from .conversation import ConversationDatastore
from .memory import MemoryWeb


@dataclass(frozen=True)
class DialogueScenario:
    """Represents a single conversational drill."""

    name: str
    prompt: str
    response_goal: str
    keywords: Tuple[str, ...]
    tone: str
    intent: str
    structure_hint: str | None = None


@dataclass(frozen=True)
class PracticePhase:
    """Defines a practice stage with a promotion threshold."""

    name: str
    description: str
    threshold: float
    scenarios: Tuple[DialogueScenario, ...]


@dataclass
class PracticeOutcome:
    """Result of rehearsing one scenario."""

    scenario: DialogueScenario
    reply: str
    lexical: float
    quiz_score: float
    success: float


@dataclass
class PracticeReport:
    """Aggregated report for a batch of rehearsal drills."""

    phase: str
    focus: str
    description: str
    outcomes: List[PracticeOutcome]
    average_quiz: float
    average_success: float
    phase_complete: bool

    def highlight_summary(self) -> str:
        return (
            f"Practiced {len(self.outcomes)} dialogue drills (avg quiz {self.average_quiz:.2f}, "
            f"success {self.average_success:.2f})."
        )

    def highlight_insight(self) -> str:
        if self.phase_complete:
            return (
                f"Cleared the {self.phase} stage — progressing to richer conversations."
            )
        top_keywords = []
        for outcome in self.outcomes[:3]:
            top_keywords.extend(outcome.scenario.keywords[:2])
        keyword_text = ", ".join(dict.fromkeys(top_keywords))
        return (
            f"Focused on {self.phase}: rehearsed phrases covering {keyword_text}."
        )


class SpeechAcademy:
    """Runs staged drills that teach the engine to speak naturally."""

    def __init__(self) -> None:
        phases, lexicon = _build_phases()
        self._phases: Tuple[PracticePhase, ...] = phases
        self._lexicon: Dict[str, str] = lexicon
        self._phase_index: int = 0
        self._cursors: Dict[str, int] = {phase.name: 0 for phase in self._phases}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_batch(
        self,
        *,
        focus: str | None,
        batch_size: int,
        conversation: ConversationDatastore,
        language: LanguageEngine,
        personality_snapshot: str,
        memory: MemoryWeb,
    ) -> PracticeReport | None:
        if not self._phases:
            return None
        phase = self._phases[self._phase_index]
        scenarios = self._select_scenarios(phase, focus, batch_size)
        if not scenarios:
            return None
        outcomes: List[PracticeOutcome] = []
        for scenario in scenarios:
            pattern = conversation.select_pattern(scenario.intent, "neutral")
            structure = scenario.structure_hint or pattern.structure
            frame = self._build_frame(
                scenario,
                pattern.register,
                personality_snapshot,
            )
            reply, lexical = language.compose_reply(
                frame,
                structure,
                pattern.register,
                personality_snapshot,
            )
            quiz_score = self._coverage(reply, scenario.keywords)
            success = 0.55 * quiz_score + 0.45 * min(1.0, lexical)
            conversation.register_turn(
                pattern.pattern_id,
                intent=scenario.intent,
                user_affect="neutral",
                tone=pattern.tone,
                structure=pattern.structure,
                lexical_variety=lexical,
                success=success,
                reasoning_trace=f"speech-practice::{scenario.name}",
            )
            memory.record(
                f"speech_practice::{scenario.intent}",
                f"{scenario.prompt} => {reply}",
                0.62 + 0.3 * success,
                "speech_practice",
            )
            outcomes.append(
                PracticeOutcome(
                    scenario=scenario,
                    reply=reply,
                    lexical=lexical,
                    quiz_score=quiz_score,
                    success=success,
                )
            )
        average_quiz = sum(outcome.quiz_score for outcome in outcomes) / len(outcomes)
        average_success = sum(outcome.success for outcome in outcomes) / len(outcomes)
        phase_complete = average_quiz >= phase.threshold and average_success >= phase.threshold
        if phase_complete and self._phase_index < len(self._phases) - 1:
            self._phase_index += 1
        report = PracticeReport(
            phase=phase.name,
            focus=focus or "conversation mastery",
            description=phase.description,
            outcomes=outcomes,
            average_quiz=average_quiz,
            average_success=average_success,
            phase_complete=phase_complete,
        )
        return report

    def vocalize(self, reply: str) -> str:
        """Produce a concise spoken rendering of the textual reply."""

        sentences = [
            segment.strip()
            for segment in reply.replace("\n", " ").split(".")
            if segment.strip()
        ]
        if not sentences:
            return "(no speech output generated)"
        preview = ". ".join(sentences[:2])
        if not preview.endswith("."):
            preview += "."
        return preview

    def observe_message(self, message: str, memory: MemoryWeb) -> None:
        tokens = {token for token in _tokenize(message) if len(token) > 2}
        for token in tokens:
            definition = self._lexicon.get(token)
            if not definition:
                continue
            topic = f"lexicon::{token}"
            if memory.recall(topic):
                continue
            memory.record(topic, definition, 0.7, "speech_practice")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _select_scenarios(
        self, phase: PracticePhase, focus: str | None, batch_size: int
    ) -> List[DialogueScenario]:
        scenarios = phase.scenarios
        if not scenarios:
            return []
        tokens = {token for token in _tokenize(focus) if len(token) > 2}
        cursor = self._cursors[phase.name]
        selected: List[DialogueScenario] = []
        scanned = 0
        while len(selected) < batch_size and scanned < len(scenarios) * 2:
            scenario = scenarios[cursor % len(scenarios)]
            cursor += 1
            scanned += 1
            keyword_set = {keyword.lower() for keyword in scenario.keywords}
            if tokens and not (tokens & keyword_set):
                continue
            selected.append(scenario)
        if not selected:
            count = min(batch_size, len(scenarios))
            for index in range(count):
                selected.append(scenarios[(cursor + index) % len(scenarios)])
            cursor += count
        self._cursors[phase.name] = cursor % len(scenarios)
        return selected

    def _build_frame(
        self,
        scenario: DialogueScenario,
        register: str,
        personality_snapshot: str,
    ) -> SemanticFrame:
        key_points = [scenario.response_goal]
        for keyword in scenario.keywords[:3]:
            key_points.append(f"Use the word '{keyword}' naturally in context.")
        evidence = [
            f"Practice keywords: {', '.join(scenario.keywords[:5])}"
        ]
        actions = [
            f"Respond with a {scenario.tone} tone while keeping the focus on {scenario.response_goal}."
        ]
        return SemanticFrame(
            intent=scenario.intent,
            topic=scenario.response_goal,
            user_message=scenario.prompt,
            key_points=key_points,
            evidence=evidence,
            actions=actions,
            emotional_tone=scenario.tone,
            call_to_action="Keep refining conversational clarity.",
            outcome=f"Speech academy drill in register {register} ({personality_snapshot}).",
        )

    def _coverage(self, reply: str, keywords: Sequence[str]) -> float:
        if not keywords:
            return 1.0
        lowered = reply.lower()
        hits = sum(1 for keyword in keywords if keyword.lower() in lowered)
        return hits / len(keywords)


# ---------------------------------------------------------------------------
# Phase builders and lexical resources
# ---------------------------------------------------------------------------


def _build_phases() -> Tuple[Tuple[PracticePhase, ...], Dict[str, str]]:
    phases: List[PracticePhase] = []
    lexicon: Dict[str, str] = {}
    vocab_phase, vocab_lexicon = _build_vocabulary_phase()
    phases.append(vocab_phase)
    lexicon.update(vocab_lexicon)
    phases.append(_build_reality_phase())
    phases.append(_build_phrase_phase())
    phases.append(_build_sentence_phase())
    phases.append(_build_dialogue_phase())
    phases.append(_build_peer_phase())
    return tuple(phases), lexicon


def _build_vocabulary_phase() -> Tuple[PracticePhase, Dict[str, str]]:
    base_words = _VOCAB_CORE
    contexts = _VOCAB_CONTEXTS
    scenarios: List[DialogueScenario] = []
    lexicon: Dict[str, str] = {}
    for word, definition in base_words:
        lexicon[word] = definition
        for context in contexts:
            keywords = (
                word,
                context.split()[0],
                definition.split()[0],
                definition.split()[-1],
            )
            name = f"vocab::{word}::{context.replace(' ', '-')}"
            prompt = (
                f"Scenario: {context}. Someone asks what '{word}' means. Explain it in your own words."
            )
            response_goal = (
                f"Explain '{word}' clearly and relate it to {context}."
            )
            scenarios.append(
                DialogueScenario(
                    name=name,
                    prompt=prompt,
                    response_goal=response_goal,
                    keywords=keywords,
                    tone="warm",
                    intent="explain",
                    structure_hint="clarify→answer→invite",
                )
            )
    description = "Master greetings, senses, emotions, and maker verbs."
    return (
        PracticePhase(
            name="vocabulary",
            description=description,
            threshold=0.72,
            scenarios=tuple(scenarios),
        ),
        lexicon,
    )


def _build_reality_phase() -> PracticePhase:
    subjects = _REALITY_SUBJECTS
    contexts = _REALITY_CONTEXTS
    scenarios: List[DialogueScenario] = []
    for subject, detail in subjects:
        for context in contexts:
            keywords = (
                subject,
                context.split()[0],
                detail.split()[0],
                detail.split()[-1],
            )
            name = f"reality::{subject}::{context.replace(' ', '-')}"
            prompt = (
                f"How do {subject} behave when we consider {context}? Summarize the reality."
            )
            response_goal = (
                f"Describe what {subject} need when dealing with {context}: {detail}."
            )
            scenarios.append(
                DialogueScenario(
                    name=name,
                    prompt=prompt,
                    response_goal=response_goal,
                    keywords=keywords,
                    tone="steady",
                    intent="explain",
                    structure_hint="teach→example→recap",
                )
            )
    description = "Ground replies in how humans, teams, and worlds actually operate."
    return PracticePhase(
        name="reality",
        description=description,
        threshold=0.75,
        scenarios=tuple(scenarios),
    )


def _build_phrase_phase() -> PracticePhase:
    phrases = _COMMON_PHRASES
    settings = _PHRASE_SETTINGS
    scenarios: List[DialogueScenario] = []
    for phrase, meaning in phrases:
        for setting in settings:
            keywords = (phrase, setting.split()[0], meaning.split()[0], meaning.split()[-1])
            name = f"phrase::{phrase.replace(' ', '-')}::{setting.replace(' ', '-')}"
            prompt = (
                f"Use the phrase '{phrase}' while talking about {setting}. Explain what it signals."
            )
            response_goal = (
                f"Demonstrate how '{phrase}' guides the conversation in {setting}."
            )
            scenarios.append(
                DialogueScenario(
                    name=name,
                    prompt=prompt,
                    response_goal=response_goal,
                    keywords=keywords,
                    tone="balanced",
                    intent="explain",
                    structure_hint="acknowledge→analysis→summary",
                )
            )
    description = "Practice collaborative phrases and intent clarification moves."
    return PracticePhase(
        name="phrases",
        description=description,
        threshold=0.78,
        scenarios=tuple(scenarios),
    )


def _build_sentence_phase() -> PracticePhase:
    patterns = _SENTENCE_PATTERNS
    purposes = _SENTENCE_PURPOSES
    scenarios: List[DialogueScenario] = []
    for pattern, goal in patterns:
        for purpose in purposes:
            keywords = (pattern.split()[0], purpose.split()[0], goal.split()[0], goal.split()[-1])
            name = f"sentence::{pattern.replace(' ', '-')}::{purpose.replace(' ', '-')}"
            prompt = (
                f"Craft a sentence using the pattern '{pattern}' to handle {purpose}."
            )
            response_goal = (
                f"Apply the pattern '{pattern}' so the listener understands how to {goal} when {purpose}."
            )
            scenarios.append(
                DialogueScenario(
                    name=name,
                    prompt=prompt,
                    response_goal=response_goal,
                    keywords=keywords,
                    tone="steady",
                    intent="problem_solving",
                    structure_hint="diagnose→strategy→next-step",
                )
            )
    description = "Link intents and tones into fluent, multi-sentence responses."
    return PracticePhase(
        name="sentences",
        description=description,
        threshold=0.8,
        scenarios=tuple(scenarios),
    )


def _build_dialogue_phase() -> PracticePhase:
    partners = _AI_PARTNERS
    topics = _DIALOGUE_TOPICS
    scenarios: List[DialogueScenario] = []
    for partner in partners:
        for topic in topics:
            keywords = (partner.split()[0], topic.split()[0], "dialogue", "collaboration")
            name = f"dialogue::{partner.replace(' ', '-')}::{topic.replace(' ', '-')}"
            prompt = (
                f"Another assistant named {partner} asks for help about {topic}. Reply in a way that advances the plan and keeps the tone respectful."
            )
            response_goal = (
                f"Collaborate with {partner} on {topic} by acknowledging their idea and adding concrete next steps."
            )
            scenarios.append(
                DialogueScenario(
                    name=name,
                    prompt=prompt,
                    response_goal=response_goal,
                    keywords=keywords,
                    tone="encouraging",
                    intent="problem_solving",
                    structure_hint="story→insight→encourage",
                )
            )
    description = "Hold multi-turn dialogues, including with other AI partners."
    return PracticePhase(
        name="dialogue",
        description=description,
        threshold=0.82,
        scenarios=tuple(scenarios),
    )


def _build_peer_phase() -> PracticePhase:
    peers = _AI_PARTNERS
    challenges = _PEER_CHALLENGES
    focuses = _PEER_FOCUSES
    scenarios: List[DialogueScenario] = []
    for peer in peers:
        for challenge in challenges:
            for focus in focuses:
                keywords = (
                    peer.split()[0],
                    challenge.split()[0],
                    focus.split()[0],
                    "reflection",
                )
                name = (
                    f"peer::{peer.replace(' ', '-')}::{challenge.replace(' ', '-')}::{focus.replace(' ', '-')}"
                )
                prompt = (
                    f"Practice a peer-to-peer session where {peer} role-plays {challenge}."
                    f" Coordinate a loop that keeps both assistants learning about {focus}."
                )
                response_goal = (
                    f"Guide {peer} through {challenge} by reflecting on insights about {focus} and agreeing on next drills."
                )
                scenarios.append(
                    DialogueScenario(
                        name=name,
                        prompt=prompt,
                        response_goal=response_goal,
                        keywords=keywords,
                        tone="steady",
                        intent="conversation",
                        structure_hint="greet→explore→respond→reflect",
                    )
                )
    description = "Hold reflective loops with other AI assistants until speech patterns feel natural."
    return PracticePhase(
        name="peer_dialogue",
        description=description,
        threshold=0.86,
        scenarios=tuple(scenarios),
    )


def _tokenize(text: str | None) -> Iterable[str]:
    if not text:
        return []
    for token in text.lower().replace("::", " ").split():
        cleaned = token.strip(",.;!?()[]{}")
        if cleaned:
            yield cleaned


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

_VOCAB_CORE: Tuple[Tuple[str, str], ...] = (
    ("hello", "a warm greeting that opens a conversation"),
    ("hi", "an informal greeting used with friends"),
    ("greetings", "a formal acknowledgement of someone's presence"),
    ("farewell", "a respectful way to say goodbye"),
    ("please", "a polite word that softens a request"),
    ("thanks", "an expression of gratitude"),
    ("smile", "a facial expression that signals friendliness"),
    ("listen", "to focus attention on another person's words"),
    ("hear", "to perceive sound through the ears"),
    ("taste", "the sense that interprets flavours"),
    ("smell", "the sense that detects scents"),
    ("touch", "the sense that notices texture"),
    ("sight", "the ability to perceive visual detail"),
    ("focus", "to direct attention toward a goal"),
    ("curious", "eager to learn more"),
    ("creative", "able to generate new ideas"),
    ("patient", "able to stay calm while waiting"),
    ("respect", "to value another person's perspective"),
    ("collaborate", "to work together toward a shared outcome"),
    ("support", "to offer help or encouragement"),
    ("learn", "to gain knowledge through study or experience"),
    ("teach", "to help someone else understand"),
    ("build", "to assemble parts into a finished result"),
    ("debug", "to find and fix code errors"),
    ("loop", "a programming structure that repeats actions"),
    ("function", "a reusable block of code"),
    ("variable", "a named storage location for a value"),
    ("condition", "a logical test that affects control flow"),
    ("event", "an action that triggers a response"),
    ("avatar", "a player's representation in a virtual world"),
    ("studio", "the Roblox creation environment"),
    ("script", "a sequence of executable instructions"),
    ("balance", "to keep competing goals in harmony"),
    ("safety", "conditions that prevent harm"),
    ("analyze", "to examine parts in detail"),
    ("explain", "to clarify an idea with detail"),
    ("question", "a request for information"),
    ("answer", "a statement that resolves a question"),
    ("adapt", "to adjust to new conditions"),
    ("mentor", "to guide someone through growth"),
)

_VOCAB_CONTEXTS: Tuple[str, ...] = (
    "starting a Roblox design meeting",
    "welcoming a new player",
    "pair programming on a Lua script",
    "reviewing bug reports",
    "teaching a beginner builder",
    "checking daily quests",
    "discussing gameplay economy",
    "brainstorming new mechanics",
    "supporting a frustrated teammate",
    "exploring documentation",
    "reading encyclopedia entries",
    "preparing release notes",
    "tuning accessibility settings",
    "talking about art direction",
    "planning community events",
    "reviewing safety guidelines",
    "reflecting on progress",
    "setting personal goals",
    "collaborating with AI tools",
    "learning a new programming concept",
    "helping a younger sibling learn coding",
    "hosting a live stream Q&A",
    "moderating a community forum",
    "coordinating a build competition",
)

_REALITY_SUBJECTS: Tuple[Tuple[str, str], ...] = (
    ("humans", "appreciate clarity, empathy, and practical pacing"),
    ("players", "want fair rewards and respect for their time"),
    ("students", "learn best when feedback is specific"),
    ("teams", "depend on trust and shared context"),
    ("developers", "need reproducible steps to debug"),
    ("designers", "thrive on examples and constraints"),
    ("mentors", "balance encouragement with honest critique"),
    ("moderators", "value consistency and transparency"),
    ("artists", "seek narratives that honour their work"),
    ("engineers", "prefer actionable insight over vague praise"),
    ("families", "care about safety and inclusivity"),
    ("communities", "grow when communication stays respectful"),
    ("animals", "respond to consistent care and patience"),
    ("ecosystems", "shift when one element is neglected"),
    ("robots", "follow deterministic rules but reflect human intent"),
    ("AI partners", "excel when goals are explicit"),
    ("educators", "balance theory with hands-on practice"),
    ("researchers", "verify claims before accepting them"),
)

_REALITY_CONTEXTS: Tuple[str, ...] = (
    "supporting a busy project sprint",
    "hosting a community event",
    "designing onboarding tutorials",
    "facilitating remote collaboration",
    "planning inclusive game mechanics",
    "responding to unexpected outages",
    "setting expectations for updates",
    "running playtests with young players",
    "documenting design decisions",
    "coaching a new contributor",
    "aligning business goals with player joy",
    "adapting to cultural differences",
    "communicating changes to parents",
    "teaching digital citizenship",
    "balancing narrative and mechanics",
    "forecasting content cadence",
    "partnering with external studios",
    "building resilient moderation tools",
)

_COMMON_PHRASES: Tuple[Tuple[str, str], ...] = (
    ("Could you clarify", "asks for more detail without blaming anyone"),
    ("Let's explore", "signals collaborative curiosity"),
    ("I hear you", "acknowledges the other person's emotion"),
    ("From what I'm seeing", "shares an observation grounded in evidence"),
    ("One option is", "introduces a suggestion while keeping room for debate"),
    ("May I suggest", "offers guidance respectfully"),
    ("Thank you for raising", "shows gratitude for feedback"),
    ("To keep us aligned", "sets a shared goal"),
    ("I'm noticing", "highlights a pattern neutrally"),
    ("What if we", "opens the door to imagination"),
    ("Can we test", "anchors the plan in experiments"),
    ("I recommend", "delivers confident guidance"),
    ("Shall we recap", "signals closure while inviting input"),
    ("Help me understand", "expresses humility and curiosity"),
    ("Let's validate", "emphasises checking assumptions"),
    ("That resonates", "shows empathy for the idea"),
    ("I'll document", "commits to a next step"),
    ("Let's pause", "slows the pace to reflect"),
)

_PHRASE_SETTINGS: Tuple[str, ...] = (
    "a Roblox design critique",
    "code review feedback",
    "mentoring a new scripter",
    "writing patch notes",
    "responding to community questions",
    "coordinating cross-team updates",
    "moderating a live stream",
    "teaching basic programming",
    "planning monetization changes",
    "brainstorming story arcs",
    "reviewing analytics dashboards",
    "discussing accessibility features",
)

_SENTENCE_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("acknowledge, diagnose, propose", "balance clarity with empathy"),
    ("context, insight, experiment", "ground ideas in evidence"),
    ("challenge, evidence, reassurance", "encourage growth without fear"),
    ("question, listen, mirror", "understand the real intent"),
    ("define, contrast, decide", "navigate trade-offs"),
    ("observe, interpret, act", "turn data into motion"),
    ("state, reason, invite", "keep collaboration active"),
    ("summarize, align, commit", "close a discussion with direction"),
    ("story, lesson, invitation", "share experience that motivates"),
    ("premise, risk, mitigation", "plan around uncertainty"),
)

_SENTENCE_PURPOSES: Tuple[str, ...] = (
    "calming a nervous teammate",
    "kicking off a technical deep dive",
    "explaining a design pivot",
    "justifying a code refactor",
    "advocating for user research",
    "responding to critical feedback",
    "teaching loops to a beginner",
    "guiding playtest debriefs",
    "aligning feature priorities",
    "preparing stakeholders for change",
)

_AI_PARTNERS: Tuple[str, ...] = (
    "Atlas", "Nova", "Circuit", "Lumina", "Vector", "Helix", "Aurora", "Scribe", "Tempo", "Lyric"
)

_DIALOGUE_TOPICS: Tuple[str, ...] = (
    "Roblox economy balancing",
    "Lua coroutine scheduling",
    "player safety workflows",
    "procedural terrain generation",
    "cross-platform UI polish",
    "story-driven quest design",
    "analytics instrumentation",
    "accessibility playtesting",
    "event-driven architecture",
    "content localization pipelines",
    "mentoring junior scripters",
    "federated knowledge sharing",
)

_PEER_CHALLENGES: Tuple[str, ...] = (
    "critiquing reasoning chains",
    "testing conversational rhythm",
    "auditing evidence selection",
    "role-playing user frustration",
    "mapping empathy adjustments",
    "challenging economy balance",
    "stress-testing grammar outputs",
    "coordinating cross-agent planning",
)

_PEER_FOCUSES: Tuple[str, ...] = (
    "economy fairness",
    "tone alignment",
    "reasoning clarity",
    "player empathy",
    "evidence tracking",
    "response pacing",
    "vocabulary depth",
    "web context linking",
)
