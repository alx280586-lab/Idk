"""Runtime helpers shared by CLI, console, and server interfaces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from ai_system.config import DEFAULT_CONFIG, SystemConfig
from ai_system.core.memory import EpisodicMemory, KnowledgeBase
from ai_system.core.reasoner import Reasoner


def _default_score(strategy_name: str) -> float:
    """Return a heuristic score used by stub evaluators."""

    lowered = strategy_name.lower()
    if "script" in lowered:
        return 0.88
    if "conversation" in lowered:
        return 0.82
    return 0.75


def _make_stub_evaluator(score: float) -> Callable[[str], float]:
    def _evaluate(_: str) -> float:
        return score

    return _evaluate


def _build_evaluators(config: SystemConfig) -> Dict[str, Callable[[str], float]]:
    """Create deterministic evaluator stubs based on configured strategies."""

    evaluators: Dict[str, Callable[[str], float]] = {}
    for name in config.evaluation_strategies:
        evaluators[name] = _make_stub_evaluator(_default_score(name))
    if not evaluators:
        evaluators["default"] = _make_stub_evaluator(0.8)
    return evaluators


@dataclass
class RuntimeContext:
    """Container bundling runtime objects for interactive interfaces."""

    config: SystemConfig
    knowledge: KnowledgeBase
    memory: EpisodicMemory
    reasoner: Reasoner


def create_runtime(config: SystemConfig | None = None) -> RuntimeContext:
    """Instantiate shared runtime dependencies for interfaces."""

    active_config = config or DEFAULT_CONFIG
    active_config.data_root.mkdir(parents=True, exist_ok=True)
    knowledge = KnowledgeBase(active_config.data_root / "knowledge")
    memory = EpisodicMemory()
    reasoner = Reasoner(knowledge, _build_evaluators(active_config))
    return RuntimeContext(active_config, knowledge, memory, reasoner)

