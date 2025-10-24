"""CLI entry-point for the Luau Synthesis Lab chatbot."""
from __future__ import annotations

from luau_lab import (
    DialogueEngine,
    LabConfig,
    LuauSynthesizer,
    RetrievalClient,
    TrainingSuite,
    load_config,
)


def bootstrap_engine() -> DialogueEngine:
    config = load_config()
    retriever = RetrievalClient(config.get_allowed_sources())
    trainer = TrainingSuite(config, retriever=retriever)
    synthesizer = LuauSynthesizer(trainer.heuristics)
    engine = DialogueEngine(
        config=config,
        synthesizer=synthesizer,
        retriever=retriever,
        trainer=trainer,
    )
    return engine


def main() -> None:
    engine = bootstrap_engine()
    persona_name = engine.persona.get("name", "Lab")
    print(f"[{persona_name}] {engine._persona_pick('greeting', 'Hello! Ready to build?')}")
    print("Type 'quit' to exit. Use 'train' to refresh heuristics.")

    while True:
        try:
            message = input("You> ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if message.strip().lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        reply = engine.respond(message)
        print(f"{persona_name}> {reply}\n")
        engine.remember(message, reply)


if __name__ == "__main__":
    main()
