"""Command line interface for operating the organic scripting AI."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Dict

from ai_system.config import DEFAULT_CONFIG, SystemConfig
from ai_system.core.memory import EpisodicMemory, KnowledgeBase, MemoryTrace
from ai_system.core.reasoner import Reasoner, Thought


def noop_evaluator(_: str) -> float:
    return 0.75


def build_reasoner(config: SystemConfig) -> Reasoner:
    knowledge = KnowledgeBase(config.data_root / "knowledge")
    evaluators: Dict[str, Callable[[str], float]] = {
        name: noop_evaluator for name in config.evaluation_strategies
    }
    return Reasoner(knowledge, evaluators)


def run_session(config: SystemConfig | None = None) -> None:
    config = config or DEFAULT_CONFIG
    knowledge = KnowledgeBase(config.data_root / "knowledge")
    episodic = EpisodicMemory()
    reasoner = build_reasoner(config)

    parser = argparse.ArgumentParser(description="Organic scripting AI session")
    parser.add_argument("goal", help="High-level objective for the session")
    parser.add_argument(
        "--keywords",
        help="Space separated keywords for the knowledge base",
        default="",
    )
    parser.add_argument(
        "--artifact",
        help="Script or conversation snippet to evaluate",
        default="",
    )
    args = parser.parse_args()

    thought: Thought = reasoner.brainstorm(args.goal, {"keywords": args.keywords})
    print("Thought process:")
    for item in thought.considerations:
        print(f" - {item}")
    print(f"Conclusion: {thought.conclusion} (confidence={thought.confidence:.2f})")

    if args.artifact:
        evaluations = reasoner.evaluate(args.artifact)
        print("Evaluations:")
        for name, score in evaluations.items():
            print(f" - {name}: {score:.2f}")

    trace = MemoryTrace(args.goal, args.artifact or thought.conclusion, thought.confidence, ["session"])
    episodic.record(trace)
    stored_path = knowledge.store(f"session_{trace.score:.2f}", trace.response)
    print(f"Stored session knowledge at {stored_path}")


def main() -> None:
    run_session()


if __name__ == "__main__":
    main()
