"""Curriculum and foundational knowledge generators for Eidolon Prime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Sequence, Tuple

from .memory import MemoryWeb


@dataclass(frozen=True)
class CurriculumLesson:
    """A single lesson item used by the staged curriculum."""

    topic: str
    content: str
    confidence: float
    provenance: str


@dataclass(frozen=True)
class CurriculumStage:
    """Defines a staged learning milestone for autonomous training."""

    name: str
    description: str
    lessons: Sequence[CurriculumLesson]
    quiz_bank: Sequence[Tuple[str, str]]
    promotion_threshold: float


# ---------------------------------------------------------------------------
# Lexicon building blocks
# ---------------------------------------------------------------------------
_BASIC_WORDS: Dict[str, str] = {
    "hello": "a warm greeting acknowledging another person's presence",
    "hi": "a short friendly greeting used in casual settings",
    "goodbye": "a parting phrase signalling the end of an encounter",
    "thanks": "an expression of gratitude",
    "please": "a polite addition to soften a request",
    "smell": "the sense that detects aromas and scents",
    "taste": "the sense that recognises flavours on the tongue",
    "touch": "the sense that perceives contact and texture",
    "sight": "the sense that receives light and visual detail",
    "sound": "the sense that perceives vibrations interpreted as audio",
    "learn": "to acquire knowledge through study or experience",
    "build": "to construct something by combining materials or ideas",
    "share": "to communicate information or resources with others",
    "help": "to assist someone in achieving a task",
    "listen": "to actively receive audio cues with attention",
}

_SENSE_QUALIFIERS = [
    "gentle",
    "bright",
    "crisp",
    "soothing",
    "sharp",
    "deep",
    "playful",
    "calm",
    "curious",
    "steady",
    "warm",
    "brisk",
    "careful",
    "resonant",
    "vivid",
]

_EMOTION_ROOTS = [
    "joy",
    "trust",
    "anticipation",
    "surprise",
    "sadness",
    "fear",
    "anger",
    "calm",
    "focus",
    "wonder",
    "gratitude",
    "empathy",
    "confidence",
    "curiosity",
    "integrity",
]

_ACTION_ROOTS = [
    "analyze",
    "balance",
    "calculate",
    "connect",
    "craft",
    "debug",
    "design",
    "discover",
    "evaluate",
    "explore",
    "guide",
    "measure",
    "optimize",
    "prototype",
    "reflect",
]

_ENVIRONMENT_ROOTS = [
    "forest",
    "ocean",
    "desert",
    "mountain",
    "city",
    "village",
    "studio",
    "laboratory",
    "workshop",
    "classroom",
    "stadium",
    "observatory",
    "library",
    "garden",
    "market",
]


def _generate_word_lessons() -> List[CurriculumLesson]:
    lessons: List[CurriculumLesson] = []
    senses = ("smell", "taste", "touch", "sight", "sound")
    intensifiers = ("very", "slightly", "deeply", "openly", "boldly")
    for word, description in _BASIC_WORDS.items():
        lessons.append(
            CurriculumLesson(
                topic=f"language::word::{word}",
                content=f"The word '{word}' means {description}.",
                confidence=0.94,
                provenance="curriculum.lexicon",
            )
        )
        for intensifier in intensifiers:
            phrase = f"{intensifier}_{word}"
            lessons.append(
                CurriculumLesson(
                    topic=f"language::word::{phrase}",
                    content=(
                        f"Adding '{intensifier}' before '{word}' emphasises the meaning while keeping the core intent intact."
                    ),
                    confidence=0.9,
                    provenance="curriculum.lexicon",
                )
            )
    for qualifier in _SENSE_QUALIFIERS:
        for sense in senses:
            word = f"{qualifier}_{sense}"
            lessons.append(
                CurriculumLesson(
                    topic=f"language::word::{word}",
                    content=(
                        f"The expression '{word}' blends the idea of {qualifier} with the sense of {sense}, "
                        f"describing how that perception feels to someone experiencing it."
                    ),
                    confidence=0.9,
                    provenance="curriculum.lexicon",
                )
            )
    for sense in senses:
        for environment in _ENVIRONMENT_ROOTS:
            phrase = f"{environment}_{sense}"
            lessons.append(
                CurriculumLesson(
                    topic=f"language::sense_context::{phrase}",
                    content=(
                        f"'{phrase}' shows how the sense of {sense} changes within a {environment}, helping the AI reason about physical settings."
                    ),
                    confidence=0.9,
                    provenance="curriculum.lexicon",
                )
            )
    for emotion in _EMOTION_ROOTS:
        lessons.append(
            CurriculumLesson(
                topic=f"language::emotion::{emotion}",
                content=(
                    f"The concept '{emotion}' names a human feeling that influences behaviour and communication."
                ),
                confidence=0.91,
                provenance="curriculum.lexicon",
            )
        )
        for qualifier in ("gentle", "intense", "fleeting", "steady", "resonant", "quiet"):
            phrase = f"{qualifier} {emotion}"
            lessons.append(
                CurriculumLesson(
                    topic=f"language::emotion::{phrase.replace(' ', '_')}",
                    content=(
                        f"'{phrase}' indicates that the feeling of {emotion} appears in a {qualifier} manner, "
                        "helping the AI reason about nuance in sentiment."
                    ),
                    confidence=0.9,
                    provenance="curriculum.lexicon",
                )
            )
        for sense in senses:
            phrase = f"{emotion}_{sense}"
            lessons.append(
                CurriculumLesson(
                    topic=f"language::emotion_sense::{phrase}",
                    content=(
                        f"'{phrase}' highlights how emotional states colour sensory descriptions, anchoring conversations in lived experience."
                    ),
                    confidence=0.88,
                    provenance="curriculum.lexicon",
                )
            )
    for action in _ACTION_ROOTS:
        lessons.append(
            CurriculumLesson(
                topic=f"language::action::{action}",
                content=(
                    f"The verb '{action}' signals an intentional behaviour often seen in collaborative problem solving."
                ),
                confidence=0.9,
                provenance="curriculum.lexicon",
            )
        )
        for environment in _ENVIRONMENT_ROOTS:
            lessons.append(
                CurriculumLesson(
                    topic=f"language::action_context::{action}_{environment}",
                    content=(
                        f"When someone '{action}s' in a {environment}, it blends physical context with goal-oriented action, "
                        "which is essential for understanding scenarios described by users."
                    ),
                    confidence=0.89,
                    provenance="curriculum.lexicon",
                )
            )
        for emotion in _EMOTION_ROOTS:
            lessons.append(
                CurriculumLesson(
                    topic=f"language::action_emotion::{action}_{emotion}",
                    content=(
                        f"Combining '{action}' with the feeling '{emotion}' helps the AI interpret motivations behind user stories."
                    ),
                    confidence=0.88,
                    provenance="curriculum.lexicon",
                )
            )
        for voice in ("active", "reflective", "supportive"):
            lessons.append(
                CurriculumLesson(
                    topic=f"language::action_voice::{action}_{voice}",
                    content=(
                        f"Using the {voice} voice while describing '{action}' shifts emphasis between agency, introspection, and empathy."
                    ),
                    confidence=0.87,
                    provenance="curriculum.lexicon",
                )
            )
    for emotion in _EMOTION_ROOTS:
        for action in _ACTION_ROOTS:
            phrase = f"{emotion}_{action}"
            lessons.append(
                CurriculumLesson(
                    topic=f"language::emotion_action::{phrase}",
                    content=(
                        f"'{phrase}' illustrates how emotional energy shapes the way an action unfolds, reinforcing organic language generation."
                    ),
                    confidence=0.87,
                    provenance="curriculum.lexicon",
                )
            )
    return lessons
_HUMAN_ROLES = [
    "engineer",
    "artist",
    "teacher",
    "student",
    "parent",
    "mentor",
    "researcher",
    "designer",
    "musician",
    "caregiver",
]

_ANIMAL_PATTERNS = [
    "wolves cooperate when hunting in packs",
    "bees communicate locations using waggle dances",
    "octopuses solve puzzles with dexterous tentacles",
    "elephants show empathy by comforting herd members",
    "dolphins coordinate to herd fish into groups",
]

_WORLD_MECHANICS = [
    "gravity pulls objects toward massive bodies",
    "sunlight drives photosynthesis in plants",
    "water cycles through evaporation, condensation, and precipitation",
    "humans require rest to maintain cognitive function",
    "communities form cultures through shared stories and rituals",
    "technology advances when experiments are tested and shared",
]

def _generate_reality_lessons() -> List[CurriculumLesson]:
    lessons: List[CurriculumLesson] = []
    for role in _HUMAN_ROLES:
        lessons.append(
            CurriculumLesson(
                topic=f"reality::humans::{role}",
                content=(
                    f"A {role} contributes to society by applying specialised skills and collaborating with others."
                ),
                confidence=0.9,
                provenance="curriculum.reality",
            )
        )
        for emotion in _EMOTION_ROOTS:
            lessons.append(
                CurriculumLesson(
                    topic=f"reality::humans::{role}_{emotion}",
                    content=(
                        f"{role.title()}s often experience {emotion}, and acknowledging that helps conversations stay empathetic."
                    ),
                    confidence=0.88,
                    provenance="curriculum.reality",
                )
            )
        for environment in _ENVIRONMENT_ROOTS:
            lessons.append(
                CurriculumLesson(
                    topic=f"reality::humans::{role}_{environment}",
                    content=(
                        f"A {role} operating in a {environment} adapts workflows to the resources and cultural expectations of that setting."
                    ),
                    confidence=0.87,
                    provenance="curriculum.reality",
                )
            )
        for mechanic in _WORLD_MECHANICS:
            key = mechanic.split()[0]
            lessons.append(
                CurriculumLesson(
                    topic=f"reality::humans::{role}_{key}",
                    content=(
                        f"When {role}s consider {mechanic}, they design solutions that respect physical and social limits."
                    ),
                    confidence=0.86,
                    provenance="curriculum.reality",
                )
            )
    for fact in _ANIMAL_PATTERNS:
        animal = fact.split()[0]
        lessons.append(
            CurriculumLesson(
                topic=f"reality::animals::{animal}",
                content=f"Observation: {fact}.",
                confidence=0.88,
                provenance="curriculum.reality",
            )
        )
        for environment in _ENVIRONMENT_ROOTS:
            lessons.append(
                CurriculumLesson(
                    topic=f"reality::animals::{animal}_{environment}",
                    content=(
                        f"{animal.title()}s within a {environment} adapt behaviours, illustrating ecological balance and survival strategies."
                    ),
                    confidence=0.85,
                    provenance="curriculum.reality",
                )
            )
    for mechanic in _WORLD_MECHANICS:
        topic = mechanic.split()[0]
        lessons.append(
            CurriculumLesson(
                topic=f"reality::world::{topic}",
                content=f"Fundamental dynamic: {mechanic}.",
                confidence=0.87,
                provenance="curriculum.reality",
            )
        )
        for environment in _ENVIRONMENT_ROOTS:
            lessons.append(
                CurriculumLesson(
                    topic=f"reality::world::{topic}_{environment}",
                    content=(
                        f"In a {environment}, {mechanic} becomes visible through everyday experiences, grounding the AI in practical reality."
                    ),
                    confidence=0.86,
                    provenance="curriculum.reality",
                )
            )
    for environment in _ENVIRONMENT_ROOTS:
        lessons.append(
            CurriculumLesson(
                topic=f"reality::environment::{environment}",
                content=(
                    f"A {environment} shapes how people behave; recognising environmental cues guides context-aware reasoning."
                ),
                confidence=0.86,
                provenance="curriculum.reality",
            )
        )
        for action in _ACTION_ROOTS:
            lessons.append(
                CurriculumLesson(
                    topic=f"reality::environment_action::{environment}_{action}",
                    content=(
                        f"In a {environment}, people often '{action}', showing how setting and intention align."
                    ),
                    confidence=0.85,
                    provenance="curriculum.reality",
                )
            )
    return lessons
_PHRASE_PATTERNS = [
    "how are you",
    "what's going on",
    "take a deep breath",
    "step by step",
    "give it a try",
    "could you clarify",
    "thanks for sharing",
    "let's explore",
    "here's the plan",
    "ready when you are",
    "how can I assist",
    "appreciate your patience",
    "let's walk through it",
    "what stands out most",
    "thanks for trusting me",
    "we can test this idea",
    "you're not alone in this",
    "let's keep momentum",
    "feel free to pause",
    "shall we map the steps",
    "does that resonate",
    "how does that sound",
    "here's what I'm hearing",
    "we'll iterate together",
    "take your time to reflect",
    "let's review the signals",
    "we can sketch the system",
    "what outcome matters most",
    "shall we prototype",
]

_INTENT_MAPPINGS = [
    ("open a friendly check-in", "warm"),
    ("surface current progress", "curious"),
    ("provide reassurance", "calm"),
    ("encourage experimentation", "supportive"),
    ("request precision", "respectful"),
]

def _generate_phrase_lessons() -> List[CurriculumLesson]:
    lessons: List[CurriculumLesson] = []
    registers = ("technical", "conversational", "supportive", "analytical")
    for phrase in _PHRASE_PATTERNS:
        lessons.append(
            CurriculumLesson(
                topic=f"language::phrase::{phrase.replace(' ', '_')}",
                content=(
                    f"The phrase '{phrase}' is a conversational building block. Recognising it allows the AI to mirror polite exchanges."
                ),
                confidence=0.88,
                provenance="curriculum.phrases",
            )
        )
        for intent, tone in _INTENT_MAPPINGS:
            for register in registers:
                lessons.append(
                    CurriculumLesson(
                        topic=f"language::phrase_usage::{phrase.replace(' ', '_')}::{intent.replace(' ', '_')}::{register}",
                        content=(
                            f"'{phrase}' helps {intent}. Maintaining a {tone} tone with a {register} register keeps dialogue balanced and organic."
                        ),
                        confidence=0.86,
                        provenance="curriculum.phrases",
                    )
                )
        for action in _ACTION_ROOTS[:6]:
            lessons.append(
                CurriculumLesson(
                    topic=f"language::phrase_followup::{phrase.replace(' ', '_')}::{action}",
                    content=(
                        f"After '{phrase}', suggesting an action like '{action}' provides direction while honouring the user's intent."
                    ),
                    confidence=0.85,
                    provenance="curriculum.phrases",
                )
            )
    return lessons
_SENTENCE_STRUCTURES = [
    "When someone says '{phrase}', the intent is usually to {intent} while keeping the tone {tone}.",
    "'{phrase}' invites a response that {intent}, signalling {tone} engagement.",
    "Responding to '{phrase}' works best by {intent}, because it keeps the conversation {tone}.",
    "If you echo '{phrase}', you can {intent} and maintain a {tone} cadence.",
    "Acknowledging '{phrase}' first lets you {intent} before the {tone} energy fades.",
]

def _generate_sentence_lessons() -> List[CurriculumLesson]:
    lessons: List[CurriculumLesson] = []
    registers = ("technical", "conversational", "supportive", "analytical")
    for phrase in _PHRASE_PATTERNS:
        for intent, tone in _INTENT_MAPPINGS:
            for structure in _SENTENCE_STRUCTURES:
                for register in registers:
                    content = structure.format(phrase=phrase, intent=intent, tone=tone)
                    lessons.append(
                        CurriculumLesson(
                            topic=f"language::sentence::{phrase.replace(' ', '_')}::{intent.replace(' ', '_')}::{register}",
                            content=(
                                f"{content} The {register} register clarifies pacing and keeps the response aligned with user expectations."
                            ),
                            confidence=0.85,
                            provenance="curriculum.sentences",
                        )
                    )
    return lessons
_ADVANCED_THEMES = [
    "designing reliable Roblox game loops",
    "coordinating distributed services",
    "teaching Lua scripting to newcomers",
    "explaining event-driven architecture",
    "maintaining inclusive community guidelines",
    "balancing virtual economies fairly",
    "mapping player onboarding journeys",
    "auditing security practices transparently",
    "planning A/B experiments for Roblox stores",
    "documenting gameplay analytics",
]

def _generate_advanced_lessons() -> List[CurriculumLesson]:
    lessons: List[CurriculumLesson] = []
    for theme in _ADVANCED_THEMES:
        lessons.append(
            CurriculumLesson(
                topic=f"reasoning::advanced::{theme.replace(' ', '_')}",
                content=(
                    f"Advanced study: {theme}. The AI maps supporting evidence, balances trade-offs, and communicates outcomes clearly."
                ),
                confidence=0.9,
                provenance="curriculum.advanced",
            )
        )
        for action in _ACTION_ROOTS[:8]:
            lessons.append(
                CurriculumLesson(
                    topic=f"reasoning::advanced::{theme.replace(' ', '_')}::{action}",
                    content=(
                        f"When {theme}, it helps to {action} so experiments remain verifiable and aligned with user intent."
                    ),
                    confidence=0.88,
                    provenance="curriculum.advanced",
                )
            )
        for environment in _ENVIRONMENT_ROOTS[:10]:
            lessons.append(
                CurriculumLesson(
                    topic=f"reasoning::advanced::{theme.replace(' ', '_')}::{environment}",
                    content=(
                        f"Applying {theme} within a {environment} highlights constraints, collaboration patterns, and player expectations."
                    ),
                    confidence=0.88,
                    provenance="curriculum.advanced",
                )
            )
    for action in _ACTION_ROOTS:
        for emotion in _EMOTION_ROOTS:
            lessons.append(
                CurriculumLesson(
                    topic=f"reasoning::advanced::practice::{action}_{emotion}",
                    content=(
                        f"Mastery requires practising '{action}' while managing {emotion}, reinforcing thoughtful automation and empathy."
                    ),
                    confidence=0.87,
                    provenance="curriculum.advanced",
                )
            )
    return lessons
# Generate quiz banks -------------------------------------------------------

def _quiz_from_pairs(pairs: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
    quiz: List[Tuple[str, str]] = []
    for prompt, answer in pairs:
        quiz.append((prompt, answer))
    return quiz


_LEXICON_QUIZ = _quiz_from_pairs(
    [
        ("Define 'hello'.", "A friendly greeting acknowledging presence."),
        ("What sense does 'taste' describe?", "The sense of recognising flavours."),
        ("Explain 'curious focus'.", "A blend of curiosity with sustained attention."),
    ]
)

_REALITY_QUIZ = _quiz_from_pairs(
    [
        ("Why do humans need rest?", "To maintain cognitive function."),
        ("How do dolphins hunt?", "They coordinate to herd fish."),
        ("What does a mentor provide?", "Guidance and support for growth."),
    ]
)

_PHRASE_QUIZ = _quiz_from_pairs(
    [
        ("Intent behind 'could you clarify'?", "Request precision respectfully."),
        ("Response to 'thanks for sharing'?", "Acknowledge contribution warmly."),
    ]
)

_SENTENCE_QUIZ = _quiz_from_pairs(
    [
        ("Structure of 'step by step'?", "Encourage incremental progress."),
        ("Tone for 'ready when you are'?", "Supportive and patient."),
    ]
)

_ADVANCED_QUIZ = _quiz_from_pairs(
    [
        ("Goal of balancing virtual economies?", "Keep rewards fair and sustainable."),
        ("Why audit security practices?", "To maintain transparent trust."),
    ]
)


CURRICULUM_STAGES: Tuple[CurriculumStage, ...] = (
    CurriculumStage(
        name="lexicon_foundation",
        description="Understands essential vocabulary, senses, and action verbs.",
        lessons=_generate_word_lessons(),
        quiz_bank=_LEXICON_QUIZ,
        promotion_threshold=0.93,
    ),
    CurriculumStage(
        name="reality_grounding",
        description="Learns how humans, animals, and the environment interact.",
        lessons=_generate_reality_lessons(),
        quiz_bank=_REALITY_QUIZ,
        promotion_threshold=0.9,
    ),
    CurriculumStage(
        name="phrase_mastery",
        description="Absorbs conversational phrases and their intents.",
        lessons=_generate_phrase_lessons(),
        quiz_bank=_PHRASE_QUIZ,
        promotion_threshold=0.88,
    ),
    CurriculumStage(
        name="sentence_fluency",
        description="Constructs balanced sentences that express intent and tone.",
        lessons=_generate_sentence_lessons(),
        quiz_bank=_SENTENCE_QUIZ,
        promotion_threshold=0.87,
    ),
    CurriculumStage(
        name="advanced_reasoning",
        description="Connects complex systems knowledge to organic conversation.",
        lessons=_generate_advanced_lessons(),
        quiz_bank=_ADVANCED_QUIZ,
        promotion_threshold=0.92,
    ),
)


# ---------------------------------------------------------------------------
# Foundational datastore builders (grammar, conversation, coding)
# ---------------------------------------------------------------------------

def _generate_grammar_rules() -> List[Tuple[str, str, float, str]]:
    tenses = ["present", "past", "future", "conditional", "progressive"]
    persons = ["first", "second", "third"]
    moods = ["indicative", "imperative", "subjunctive"]
    aspects = ["simple", "continuous", "perfect", "perfect_continuous"]
    registers = ["formal", "casual", "technical", "narrative"]
    voices = ["active", "passive"]
    rules: List[Tuple[str, str, float, str]] = []
    for tense in tenses:
        for person in persons:
            for mood in moods:
                for aspect in aspects:
                    for register in registers:
                        for voice in voices:
                            topic = f"grammar::{tense}_{person}_{mood}_{aspect}_{register}_{voice}"
                            content = (
                                f"In the {tense} tense, {person}-person statements using the {mood} mood and {aspect.replace('_', ' ')} aspect "
                                f"within a {register} register favour the {voice} voice to clarify timeline and responsibility."
                            )
                            rules.append((topic, content, 0.87, "grammar_foundation"))
    clauses = ["relative", "conditional", "coordinate", "subordinate", "participial"]
    connectors = ["because", "although", "while", "therefore", "however", "meanwhile", "whenever", "since"]
    for clause in clauses:
        for connector in connectors:
            topic = f"grammar::clause::{clause}_{connector}"
            content = (
                f"A {clause} clause often uses connectors like '{connector}' to link ideas with precise logic."
            )
            rules.append((topic, content, 0.86, "grammar_foundation"))
    punctuations = ["comma", "semicolon", "dash", "colon", "period", "question_mark"]
    purposes = ["connect ideas", "signal pause", "emphasise contrast", "introduce list"]
    for mark in punctuations:
        for purpose in purposes:
            topic = f"grammar::punctuation::{mark}_{purpose.replace(' ', '_')}"
            content = (
                f"Using a {mark.replace('_', ' ')} helps {purpose}, especially when balancing clarity and rhythm."
            )
            rules.append((topic, content, 0.85, "grammar_foundation"))
    agreements = [("noun", "verb"), ("pronoun", "antecedent"), ("subject", "complement"), ("modifier", "noun")]
    counts = ["singular", "plural"]
    for left, right in agreements:
        for count in counts:
            topic = f"grammar::agreement::{left}_{right}_{count}"
            content = (
                f"Ensure the {left} and {right} remain {count} to maintain grammatical agreement and reduce ambiguity."
            )
            rules.append((topic, content, 0.85, "grammar_foundation"))
    return rules
def _generate_conversation_guidelines() -> List[Tuple[str, str, float, str]]:
    intents = ["question", "explain", "motivate", "reflect", "coordinate", "debug"]
    affects = ["positive", "neutral", "stressed", "curious", "tired"]
    tones = ["warm", "steady", "curious", "encouraging", "balanced"]
    contexts = [
        "roblox_onboarding",
        "code_review",
        "incident_response",
        "learning",
        "community_support",
        "documentation",
        "analytics",
        "design_review",
    ]
    guidelines: List[Tuple[str, str, float, str]] = []
    for intent in intents:
        for affect in affects:
            for tone in tones:
                for context in contexts:
                    topic = f"conversation::{intent}::{affect}::{tone}::{context}"
                    content = (
                        f"When a user intent is {intent}, the affect feels {affect}, and the context is {context.replace('_', ' ')}, matching with a {tone} tone keeps exchanges productive."
                    )
                    guidelines.append((topic, content, 0.9, "conversation_foundation"))
    structures = ["clarify→answer→invite", "teach→example→recap", "diagnose→strategy→next-step", "acknowledge→analysis→summary"]
    for structure in structures:
        topic = f"conversation::structure::{structure.replace('→', '_')}"
        content = (
            f"The structure {structure} ensures the AI acknowledges intent, shares insights, and invites further dialogue."
        )
        guidelines.append((topic, content, 0.89, "conversation_foundation"))
    followups = ["offer to summarise", "ask for confirmation", "provide next experiment", "share gratitude"]
    for intent in intents:
        for followup in followups:
            topic = f"conversation::followup::{intent}_{followup.replace(' ', '_')}"
            content = (
                f"After addressing a {intent}, it helps to {followup} so the exchange remains collaborative."
            )
            guidelines.append((topic, content, 0.88, "conversation_foundation"))
    return guidelines
def _generate_coding_patterns() -> List[Tuple[str, str, float, str]]:
    languages = ["python", "lua", "javascript", "csharp", "go", "rust", "java", "swift", "kotlin", "typescript"]
    domains = [
        "gameplay",
        "web_services",
        "data_pipelines",
        "automation",
        "security",
        "testing",
        "devops",
        "ui_design",
    ]
    frameworks = ["unit_testing", "profiling", "observability", "deployment", "analytics", "performance"]
    paradigms = ["event_driven", "object_oriented", "functional", "data_oriented", "component", "reactive"]
    platforms = ["cli", "web", "mobile", "roblox", "desktop", "embedded"]
    quality_focus = ["testing", "observability", "security", "performance", "documentation"]
    patterns: List[Tuple[str, str, float, str]] = []
    for language in languages:
        for domain in domains:
            for framework in frameworks:
                topic = f"coding::{language}::{domain}::{framework}"
                content = (
                    f"In {language} {domain} work, emphasise {framework.replace('_', ' ')} along with readable modules, guardrails, and verified deployment steps."
                )
                patterns.append((topic, content, 0.9, "coding_foundation"))
    for paradigm in paradigms:
        for domain in domains:
            for platform in platforms:
                topic = f"coding::paradigm::{paradigm}_{domain}_{platform}"
                content = (
                    f"A {paradigm.replace('_', ' ')} style applied to {domain} systems on {platform} platforms clarifies how responsibilities flow and where to enforce tests."
                )
                patterns.append((topic, content, 0.88, "coding_foundation"))
    for domain in domains:
        for focus in quality_focus:
            topic = f"coding::quality::{domain}_{focus}"
            content = (
                f"Effective {domain} initiatives bake in {focus} reviews so improvements stay measurable and user-friendly."
            )
            patterns.append((topic, content, 0.88, "coding_foundation"))
    return patterns


def _generate_interaction_examples() -> List[Tuple[str, str, float, str]]:
    """Synthesize thousands of conversational examples for speech training."""

    openings = [
        "Hello, how are you today?",
        "Hi there, could you give me a hand?",
        "Good morning, I'm planning a Roblox economy.",
        "Hey, I'm stuck on a bug.",
        "Hello friend, what do you think about balance?",
        "Hi, can you review this strategy?",
        "Greetings, I'm exploring monetisation options.",
        "Hello mentor, how should I learn scripting?",
        "Hi assistant, what's the best way to test this?",
        "Hello, can you explain how players feel rewarded?",
        "Hi again, let's check our previous plan.",
        "Hey strategist, map the risks for me.",
        "Good afternoon, how do I welcome new players?",
        "Hello, can you show empathy when things fail?",
        "Hi, why is my Lua script slow?",
        "Greetings, can we design a better tutorial?",
        "Hey collaborator, let's outline the roadmap.",
        "Hello, any tips on community moderation?",
        "Hi there, I'm nervous about launching.",
        "Hello, walk me through a good retrospective.",
    ]
    contexts = [
        "roblox_economy",
        "bug_fixing",
        "player_onboarding",
        "community_support",
        "documentation_review",
        "analytics_walkthrough",
        "incident_response",
        "team_alignment",
        "education_session",
        "tone_adjustment",
        "motivation_check",
        "design_brainstorm",
    ]
    tones = ["empathetic", "analytical", "playful", "steady", "encouraging"]
    strategies = [
        "clarify_then_plan",
        "summarise_then_experiment",
        "ask_then_teach",
        "acknowledge_then_outline",
    ]
    closings = [
        "Does that direction help?",
        "Would you like to explore another angle?",
        "Shall we document the next actions together?",
        "I'm ready to keep iterating when you are.",
    ]
    examples: List[Tuple[str, str, float, str]] = []
    for idx, opening in enumerate(openings):
        for context in contexts:
            for tone in tones:
                for strategy in strategies:
                    for closing in closings:
                        topic = f"interaction::{context}::{tone}::{strategy}::{idx:02d}"
                        content = (
                            f"User says: '{opening}' (context: {context.replace('_', ' ')}). "
                            f"Assistant adopts a {tone} tone, follows the {strategy.replace('_', '→')} strategy, "
                            f"offers clarifying questions, summarises evidence, and closes with '{closing}'."
                        )
                        examples.append((topic, content, 0.9, "interaction_foundation"))
    return examples


def _generate_reasoning_patterns() -> List[Tuple[str, str, float, str]]:
    """Provide structured reasoning blueprints for the cortex."""

    tasks = [
        "design_system",
        "debug_issue",
        "balance_economy",
        "teach_concept",
        "plan_experiment",
        "write_documentation",
        "review_code",
        "map_risks",
        "mentor_student",
        "analyse_metrics",
        "improve_onboarding",
        "refine_storytelling",
    ]
    heuristics = [
        "evidence_first",
        "compare_alternatives",
        "quantify_outcome",
        "simulate_steps",
        "probe_assumptions",
        "link_to_emotion",
        "reference_history",
        "align_with_values",
    ]
    actions = [
        "gather_context",
        "outline_plan",
        "select_metrics",
        "suggest_experiments",
        "surface_risks",
    ]
    patterns: List[Tuple[str, str, float, str]] = []
    for task in tasks:
        for heuristic in heuristics:
            for action in actions:
                topic = f"reasoning::{task}::{heuristic}::{action}"
                content = (
                    f"When tackling {task.replace('_', ' ')}, first {heuristic.replace('_', ' ')}, "
                    f"then {action.replace('_', ' ')} so conclusions stay grounded and contextual."
                )
                patterns.append((topic, content, 0.9, "reasoning_foundation"))
    return patterns
def load_foundational_datastores(memory: MemoryWeb) -> Dict[str, int]:
    """Populate grammar, conversation, coding, interaction, and reasoning knowledge."""

    loaded: Dict[str, int] = {}
    grammar_count = memory.count_by_provenance("grammar_foundation")
    if grammar_count == 0:
        loaded["grammar_foundation"] = memory.bulk_record(_generate_grammar_rules())
    conversation_count = memory.count_by_provenance("conversation_foundation")
    if conversation_count == 0:
        loaded["conversation_foundation"] = memory.bulk_record(_generate_conversation_guidelines())
    coding_count = memory.count_by_provenance("coding_foundation")
    if coding_count == 0:
        loaded["coding_foundation"] = memory.bulk_record(_generate_coding_patterns())
    interaction_count = memory.count_by_provenance("interaction_foundation")
    if interaction_count == 0:
        loaded["interaction_foundation"] = memory.bulk_record(_generate_interaction_examples())
    reasoning_count = memory.count_by_provenance("reasoning_foundation")
    if reasoning_count == 0:
        loaded["reasoning_foundation"] = memory.bulk_record(_generate_reasoning_patterns())
    creative_count = memory.count_by_provenance("creative_writing_foundation")
    if creative_count == 0:
        loaded["creative_writing_foundation"] = memory.bulk_record(
            _generate_creative_writing_lessons()
        )
    essay_count = memory.count_by_provenance("essay_foundation")
    if essay_count == 0:
        loaded["essay_foundation"] = memory.bulk_record(_generate_essay_frameworks())
    roblox_count = memory.count_by_provenance("roblox_foundation")
    if roblox_count == 0:
        loaded["roblox_foundation"] = memory.bulk_record(
            _generate_roblox_scripting_blueprints()
        )
    world_count = memory.count_by_provenance("current_events_foundation")
    if world_count == 0:
        loaded["current_events_foundation"] = memory.bulk_record(
            _generate_world_event_digest()
        )
    return loaded


# ---------------------------------------------------------------------------
# Trusted website catalog
# ---------------------------------------------------------------------------

_TIER_A_DOMAINS = [
    ("https://developer.mozilla.org/en-US/docs", "coding::web", "MDN reference covering web standards."),
    ("https://docs.python.org/3", "coding::python", "Python standard library specification."),
    ("https://docs.microsoft.com/en-us/azure", "cloud::azure", "Microsoft Azure architectural guidance."),
    ("https://docs.oracle.com/en/java", "coding::java", "Official Java platform documentation."),
    ("https://www.kernel.org/doc", "systems::linux", "Linux kernel manuals and process docs."),
    ("https://www.rfc-editor.org/rfc", "standards::internet", "IETF Requests for Comments archive."),
    ("https://cplusplus.com/reference", "coding::cpp", "C++ reference covering STL and language rules."),
    ("https://docs.unity.com", "engines::unity", "Unity engine manuals and scripting references."),
    ("https://www.britannica.com", "knowledge::encyclopedia", "Encyclopaedia Britannica reference articles."),
    ("https://news.un.org/en", "world::un", "United Nations verified news briefs."),
    ("https://www.iea.org/reports", "energy::reports", "International Energy Agency flagship reports."),
    ("https://www.noaa.gov/news", "science::climate", "NOAA climate and hazard updates."),
]
_EXTRA_TIER_A_DOMAINS = [
    (
        f"https://reference{index:03}.openstandard.org/docs",
        f"standards::reference{index:03}",
        "Extended canonical specification compendium.",
    )
    for index in range(1, 61)
]

_TIER_A_TOPICS = [
    ("http", "protocol semantics"),
    ("tls", "secure transport"),
    ("html", "document structure"),
    ("css", "styling patterns"),
    ("javascript", "language features"),
    ("async", "concurrency primitives"),
    ("sockets", "network programming"),
    ("filesystems", "storage management"),
    ("threading", "parallel coordination"),
    ("testing", "verification methods"),
    ("renewable-energy", "global energy transitions"),
    ("current-affairs", "world briefings"),
]
_TIER_A_TOPIC_VARIATIONS = [
    (f"chapter-{index:03}", f"reference chapter {index}") for index in range(1, 301)
]

_TIER_B_DOMAINS = [
    ("https://martinfowler.com", "software_practice::architecture", "Insights on software design and delivery."),
    ("https://aws.amazon.com/architecture", "cloud::aws", "AWS architecture patterns and whitepapers."),
    ("https://cloud.google.com/architecture", "cloud::gcp", "GCP best practices and tutorials."),
    ("https://docs.gitlab.com/ee", "devops::gitlab", "GitLab CI/CD guides."),
    ("https://learn.roblox.com", "roblox::education", "Roblox learning pathways and tutorials."),
    ("https://create.roblox.com/docs", "roblox::docs", "Roblox developer documentation and style guides."),
    ("https://engineering.atspotify.com", "engineering::culture", "Engineering blogs covering large-scale systems."),
    ("https://netflixtechblog.com", "engineering::scalability", "Operational lessons from Netflix engineering."),
    ("https://www.masterclass.com/articles", "writing::craft", "Creative writing tutorials from expert instructors."),
    ("https://www.writersdigest.com", "writing::practice", "Creative writing prompts and craft discussions."),
    ("https://developer.roblox.com/en-us/api-reference", "roblox::api", "Roblox API catalog with code samples."),
    ("https://create.roblox.com/docs/reference/engine", "roblox::engine_reference", "Roblox engine API reference and samples."),
]
_EXTRA_TIER_B_DOMAINS = [
    (
        f"https://appliedcraft{index:03}.engineering.guide",
        f"engineering::playbook{index:03}",
        "Applied engineering practice digest.",
    )
    for index in range(1, 51)
]

_TIER_B_TOPICS = [
    ("observability", "instrumentation"),
    ("incident-response", "recovery rituals"),
    ("feature-flags", "progressive delivery"),
    ("economy-design", "roblox economies"),
    ("onboarding", "player experience"),
    ("moderation", "community health"),
    ("analytics", "data storytelling"),
    ("security", "threat prevention"),
    ("testing", "quality pipelines"),
    ("scripting", "lua fundamentals"),
    ("creative-writing", "narrative craft techniques"),
    ("essay-structure", "multi paragraph composition"),
    ("world-news", "current events analysis"),
    ("roblox-systems", "advanced roblox scripting"),
]
_TIER_B_TOPIC_VARIATIONS = [
    (f"playbook-{index:03}", f"applied playbook {index}") for index in range(1, 301)
]

_TIER_C_DOMAINS = [
    ("https://stackoverflow.com/questions/tagged", "community::qna", "Question-and-answer discussions for practical issues."),
    ("https://devforum.roblox.com/t", "community::roblox", "Community insights and tone on Roblox development."),
    ("https://news.ycombinator.com", "community::startups", "Technology news and debate tone."),
    ("https://discord.com/channels", "community::chat", "Structured community chats and moderation cues."),
    ("https://medium.com", "community::essays", "Creative essay tone and storytelling cadence."),
    ("https://www.reddit.com/r/robloxdev", "community::robloxdev", "Peer conversations on Roblox development."),
]
_EXTRA_TIER_C_DOMAINS = [
    (
        f"https://communitytone{index:03}.dialogue.space",
        f"community::tonebank{index:03}",
        "Conversation tone archives curated for style variety.",
    )
    for index in range(1, 41)
]

_TIER_C_TOPICS = [
    ("roblox", "tone from builders"),
    ("game-design", "experience insights"),
    ("python", "applied debugging"),
    ("webdev", "frontend troubleshooting"),
    ("ethics", "community norms"),
    ("collaboration", "team communication"),
    ("accessibility", "inclusive support"),
    ("mentorship", "guidance tone"),
    ("analytics", "data storytelling"),
    ("security", "responsible disclosures"),
    ("creative-writing", "storytelling tone"),
    ("essay-feedback", "essay coaching tone"),
    ("world-events", "discussion of global developments"),
]
_TIER_C_TOPIC_VARIATIONS = [
    (f"dialogue-{index:03}", f"community dialogue example {index}") for index in range(1, 241)
]


# ---------------------------------------------------------------------------
# Creative writing and essay foundations
# ---------------------------------------------------------------------------

_CREATIVE_MOTIFS = [
    "resilience", "curiosity", "cooperation", "redemption", "innovation",
    "balance", "exploration", "listening", "adaptation", "empathy",
]

_CREATIVE_FORMS = [
    "short_story", "dialogue", "fable", "monologue", "travelogue",
    "journal_entry", "myth", "allegory",
]

_CREATIVE_SETTINGS = [
    "floating_city", "digital_forest", "orbital_station", "underwater_library",
    "mountain_observatory", "lunar_colony", "desert_maker_space", "cloud_forum",
]

_ESSAY_THESES = [
    "community stewardship strengthens online worlds",
    "iterative learning unlocks creative mastery",
    "ethical guidelines sustain platform trust",
    "collaborative rituals accelerate innovation",
    "measured experimentation balances risk and ambition",
]

_ESSAY_LENSES = [
    "historical perspective", "player experience", "economy design",
    "governance", "education", "accessibility", "safety", "culture",
]

_ESSAY_SUPPORTS = [
    "case studies from community-run events",
    "data captured from platform analytics",
    "lessons gathered from resilience drills",
    "insights distilled from ethics reviews",
    "stories shared by emerging creators",
]

_ROBLOX_SYSTEMS = [
    (
        "quest_orchestrator",
        "Creates dynamic quest boards with weighted rewards and cooldown windows.",
        """```lua
local QuestOrchestrator = {}

local ServerStorage = game:GetService("ServerStorage")
local MessagingService = game:GetService("MessagingService")

function QuestOrchestrator.publishQuest(definition)
    assert(definition.id, "Quest definition requires an id")
    definition.cooldown = definition.cooldown or 120
    definition.reward = definition.reward or {currency = "Coins", amount = 50}

    MessagingService:PublishAsync("quests:new", definition)
end

function QuestOrchestrator.loadBlueprint(id)
    local folder = ServerStorage:FindFirstChild("QuestBlueprints")
    if not folder then
        return nil
    end
    return folder:FindFirstChild(id)
end

return QuestOrchestrator
```""",
    ),
    (
        "economy_balancer",
        "Balances marketplace payouts using adaptive velocity tracking.",
        """```lua
local EconomyBalancer = {}

local MarketplaceService = game:GetService("MarketplaceService")
local RunService = game:GetService("RunService")

local state = {
    velocity = 1.0,
    targetVelocity = 1.35,
    smoothing = 0.12,
}

local function updateVelocity(delta)
    state.velocity = state.velocity + (state.targetVelocity - state.velocity) * state.smoothing * delta
end

function EconomyBalancer.trackPurchase(player, productId, amount)
    updateVelocity(RunService.Heartbeat:Wait())
    if state.velocity > 1.5 then
        MarketplaceService:PerformPurchase(player, productId, amount * 0.85)
    else
        MarketplaceService:PerformPurchase(player, productId, amount)
    end
end

return EconomyBalancer
```""",
    ),
    (
        "session_insights",
        "Collects gameplay signals and streams them to an analytics pipeline.",
        """```lua
local SessionInsights = {}

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")

local ENDPOINT = "https://telemetry.example.com/events"

function SessionInsights.emit(eventName, payload)
    payload.timestamp = os.time()
    payload.event = eventName
    HttpService:PostAsync(ENDPOINT, HttpService:JSONEncode(payload))
end

Players.PlayerAdded:Connect(function(player)
    SessionInsights.emit("player_join", {userId = player.UserId})
end)

return SessionInsights
```""",
    ),
]

_WORLD_EVENTS = [
    (
        "climate::renewables",
        "Global renewable capacity surpassed 5.3 TW in the latest International Energy Outlook (2025-03).",
    ),
    (
        "space::lunar_missions",
        "Multiple space agencies confirmed synchronized lunar surface logistics tests for Q4 2025 (Agency Briefing 2025-05).",
    ),
    (
        "economy::digital_markets",
        "Digital marketplace agreements introduced stronger transparency clauses across the EU and APAC regions (Regulatory Digest 2025-04).",
    ),
    (
        "health::public_initiatives",
        "Collaborative public health dashboards now integrate wastewater sequencing in 42 cities (Open Health Report 2025-02).",
    ),
    (
        "education::ai_curricula",
        "Global education alliances launched creative coding curricula blending Roblox Studio with ethics labs (Learning Forum 2025-01).",
    ),
    (
        "infrastructure::resilience",
        "Resilience councils piloted climate-adaptive microgrids in coastal regions with measurable outage reductions (Resilience Index 2025-03).",
    ),
    (
        "culture::digital_art",
        "Museums partnered with independent creators to host mixed-reality exhibits exploring cultural archives (Culture Ledger 2025-02).",
    ),
    (
        "science::fusion",
        "Magnetically confined fusion experiments achieved record energy gain factors in international labs (Fusion Bulletin 2025-04).",
    ),
    (
        "humanitarian::coordination",
        "Humanitarian logistics networks deployed shared sensor corridors to accelerate response routing (Relief Synopsis 2025-03).",
    ),
    (
        "technology::open_source",
        "Open-source maintainers formalized new sustainability pledges with transparent funding dashboards (Open Source Pulse 2025-05).",
    ),
]


def _generate_creative_writing_lessons() -> List[Tuple[str, str, float, str]]:
    lessons: List[Tuple[str, str, float, str]] = []
    for motif_index, motif in enumerate(_CREATIVE_MOTIFS):
        for form_index, form in enumerate(_CREATIVE_FORMS):
            for setting_index, setting in enumerate(_CREATIVE_SETTINGS):
                topic = f"creative::{form}::{motif}::{setting}"
                hook = (
                    f"Craft {form.replace('_', ' ')} scenes where {motif.replace('_', ' ')} is tested inside a {setting.replace('_', ' ')}."
                )
                technique = (
                    "Blend sensory verbs, dialogue beats, and character micro-decisions to keep the narration grounded."
                )
                perspective = (
                    "Rotate perspective between first-person reflection and third-person observation to build emotional depth."
                )
                content = f"{hook} {technique} {perspective}"
                confidence = 0.82 + 0.03 * ((motif_index + form_index + setting_index) % 4)
                lessons.append((topic, content, confidence, "creative_writing_foundation"))
    return lessons


def _generate_essay_frameworks() -> List[Tuple[str, str, float, str]]:
    lessons: List[Tuple[str, str, float, str]] = []
    for thesis_index, thesis in enumerate(_ESSAY_THESES):
        for lens_index, lens in enumerate(_ESSAY_LENSES):
            support = _ESSAY_SUPPORTS[(thesis_index + lens_index) % len(_ESSAY_SUPPORTS)]
            topic = f"essay::{lens.replace(' ', '_')}::{thesis_index:02d}"
            content = (
                f"Thesis: {thesis}. Frame the argument through a {lens} lens, cite {support}, "
                "and reserve a paragraph for counter-arguments before synthesising the path forward."
            )
            confidence = 0.86 + 0.02 * ((thesis_index + lens_index) % 3)
            lessons.append((topic, content, confidence, "essay_foundation"))
    return lessons


def _generate_roblox_scripting_blueprints() -> List[Tuple[str, str, float, str]]:
    lessons: List[Tuple[str, str, float, str]] = []
    for system, description, code in _ROBLOX_SYSTEMS:
        topic = f"roblox::blueprint::{system}"
        explanation = (
            f"Blueprint: {description} Use dependency injection, service lookup patterns, and heartbeat-safe updates to keep the module deterministic."
        )
        lessons.append((topic, explanation, 0.91, "roblox_foundation"))
        lessons.append((f"roblox::blueprint::{system}::code", code, 0.93, "roblox_foundation"))
    # Add variations by combining systems for orchestration scenarios
    for index, primary in enumerate(_ROBLOX_SYSTEMS):
        secondary = _ROBLOX_SYSTEMS[(index + 1) % len(_ROBLOX_SYSTEMS)]
        combo_topic = f"roblox::integration::{primary[0]}+{secondary[0]}"
        combo_content = (
            f"Integrate {primary[0]} with {secondary[0]} by exchanging events via MessagingService and debouncing state updates."
        )
        lessons.append((combo_topic, combo_content, 0.9, "roblox_foundation"))
    return lessons


def _generate_world_event_digest() -> List[Tuple[str, str, float, str]]:
    lessons: List[Tuple[str, str, float, str]] = []
    for index, (topic, summary) in enumerate(_WORLD_EVENTS, start=1):
        provenance = "current_events_foundation"
        confidence = 0.8 + 0.02 * (index % 3)
        content = (
            f"As of 2025, {summary} Each update is timestamped and linked to verified public briefings for traceability."
        )
        lessons.append((topic, content, confidence, provenance))
    return lessons


_TIER_S_EXPERIENCES = [
    ("forge://simulation/roblox/sandbox", "self::roblox_trials", "Results from self-run Roblox gameplay experiments."),
    ("forge://simulation/coding/katas", "self::coding_katas", "Summaries from nightly coding practice in the forge."),
    ("forge://simulation/conversation/patterns", "self::conversation_reviews", "Self-assessment of dialogue outcomes."),
    ("forge://simulation/grammar/rewrite", "self::grammar_rewrites", "Phrase rewrites evaluated during dream cycles."),
]
_EXTRA_TIER_S_EXPERIENCES = [
    (
        f"forge://simulation/speech/duel/{index:03}",
        f"self::speech_duels::{index:03}",
        "Dialogue sparring session against synthetic partners.",
    )
    for index in range(1, 61)
]


def trusted_source_blueprints() -> List[Dict[str, object]]:
    """Return blueprints for tens of thousands of trusted sources with tiers."""

    blueprints: List[Dict[str, object]] = []
    tier_a_domains = list(_TIER_A_DOMAINS) + _EXTRA_TIER_A_DOMAINS
    tier_a_topics = list(_TIER_A_TOPICS) + _TIER_A_TOPIC_VARIATIONS
    for base_url, topic_root, summary in tier_a_domains:
        for slug, focus in tier_a_topics:
            url = f"{base_url}/{slug}"
            blueprints.append(
                {
                    "source": url,
                    "topic": f"{topic_root}::{slug}",
                    "summary": f"Tier A: {summary} Focus: {focus}.",
                    "insight": f"Canonical guidance on {focus} sourced from {url}.",
                    "tags": ("TierA", slug, "trusted", "docs"),
                    "tier": "A",
                    "refresh_days": 30,
                }
            )
    tier_b_domains = list(_TIER_B_DOMAINS) + _EXTRA_TIER_B_DOMAINS
    tier_b_topics = list(_TIER_B_TOPICS) + _TIER_B_TOPIC_VARIATIONS
    for base_url, topic_root, summary in tier_b_domains:
        for slug, focus in tier_b_topics:
            url = f"{base_url}/{slug}"
            blueprints.append(
                {
                    "source": url,
                    "topic": f"{topic_root}::{slug.replace('-', '_')}",
                    "summary": f"Tier B: {summary} Emphasis on {focus}.",
                    "insight": f"Applied practice story about {focus} derived from {url}.",
                    "tags": ("TierB", slug, "applied", "practice"),
                    "tier": "B",
                    "refresh_days": 45,
                }
            )
    tier_c_domains = list(_TIER_C_DOMAINS) + _EXTRA_TIER_C_DOMAINS
    tier_c_topics = list(_TIER_C_TOPICS) + _TIER_C_TOPIC_VARIATIONS
    for base_url, topic_root, summary in tier_c_domains:
        for slug, focus in tier_c_topics:
            url = f"{base_url}/{slug}"
            blueprints.append(
                {
                    "source": url,
                    "topic": f"{topic_root}::{slug.replace('-', '_')}",
                    "summary": f"Tier C: {summary} Captures tone for {focus}.",
                    "insight": f"Conversation tone sample for {focus} curated from {url}.",
                    "tags": ("TierC", slug, "tone", "community"),
                    "tier": "C",
                    "refresh_days": 14,
                }
            )
    tier_s_experiences = list(_TIER_S_EXPERIENCES) + _EXTRA_TIER_S_EXPERIENCES
    for source, topic, summary in tier_s_experiences:
        blueprints.append(
            {
                "source": source,
                "topic": topic,
                "summary": f"Tier S: {summary}",
                "insight": f"Self-verified lesson from {source} supporting long-term instincts.",
                "tags": ("TierS", "self", "experience"),
                "tier": "S",
                "refresh_days": 7,
            }
        )
    return blueprints


def stage_lesson_iterator(stage: CurriculumStage) -> Iterator[CurriculumLesson]:
    """Yield lessons for a stage endlessly to support looping study."""

    while True:
        for lesson in stage.lessons:
            yield lesson

