"""Interactive ChatWeaver inference script."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import torch

from model import ChatWeaverModel

try:
    import sentencepiece as spm
except ImportError as exc:  # pragma: no cover - runtime check
    raise ImportError("sentencepiece is required for inference") from exc


SYSTEM_PROMPT = "You are ChatWeaver, a helpful and concise AI assistant."


def load_model(checkpoint: Path, device: torch.device) -> ChatWeaverModel:
    model = ChatWeaverModel.from_checkpoint(str(checkpoint), map_location=device)
    model.eval().to(device)
    return model


def generate_response(
    model: ChatWeaverModel,
    tokenizer: spm.SentencePieceProcessor,
    history: List[str],
    device: torch.device,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
) -> str:
    prompt = "".join(history)
    input_ids = tokenizer.encode(prompt, out_type=int)
    if len(input_ids) >= model.config.context_length:
        input_ids = input_ids[-model.config.context_length :]
    input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
    with torch.no_grad():
        generated = model.generate(
            input_tensor, max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p
        )
    output_ids = generated[0, len(input_ids) :].tolist()
    return tokenizer.decode(output_ids)


def build_prompt(user_input: str, history: List[str]) -> None:
    if not history:
        history.append(f"<|system|> {SYSTEM_PROMPT}\n")
    history.append(f"<|user|> {user_input}\n")
    history.append("<|assistant|> ")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with a ChatWeaver-4B checkpoint.")
    parser.add_argument("--checkpoint", required=True, help="Path to the model checkpoint .pt file.")
    parser.add_argument("--tokenizer", required=True, help="Path to the SentencePiece tokenizer model.")
    parser.add_argument("--max-new-tokens", type=int, default=256, help="Tokens to generate per response.")
    parser.add_argument("--temperature", type=float, default=0.8, help="Sampling temperature.")
    parser.add_argument("--top-p", type=float, default=0.95, help="Top-p nucleus sampling threshold.")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = spm.SentencePieceProcessor(model_file=args.tokenizer)
    model = load_model(Path(args.checkpoint), device)

    print("ChatWeaver-4B interactive chat. Type 'exit' to stop.")
    history: List[str] = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break
        build_prompt(user_input, history)
        response = generate_response(
            model,
            tokenizer,
            history,
            device,
            args.max_new_tokens,
            args.temperature,
            args.top_p,
        )
        history[-1] += response + "\n"
        print(f"ChatWeaver: {response}")


if __name__ == "__main__":
    main()
