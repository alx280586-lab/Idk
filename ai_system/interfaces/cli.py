"""Command line interface for operating the organic scripting AI."""
from __future__ import annotations

import argparse

from ai_system.config import SystemConfig
from ai_system.core.memory import MemoryTrace
from ai_system.core.reasoner import Thought
from ai_system.interfaces.runtime import RuntimeContext, create_runtime


def run_session(config: SystemConfig | None = None) -> None:
    runtime: RuntimeContext = create_runtime(config)
    knowledge = runtime.knowledge
    episodic = runtime.memory
    reasoner = runtime.reasoner

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
