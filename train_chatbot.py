"""Entry point that stitches together the reasoning chatbot modules."""

from typing import List

import torch

from mini_chatbot import (
    ChatbotConfig,
    ReasoningChatDataset,
    SAMPLE_DIALOGUES,
    batch_iterator,
    build_model,
    describe_model,
    generate_reply,
    load_tokenizer,
    run_dummy_training,
)


def choose_device() -> torch.device:
    """Pick GPU when available, otherwise CPU."""

    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def show_tokenization(tokenizer) -> None:
    """Print token ids for USER/BOT prefixes so beginners can inspect them."""

    sample_text = "USER: hello\nBOT: hi there!"
    tokens: List[int] = tokenizer.encode(sample_text, add_special_tokens=True)
    print("Tokenization example for a short chat snippet:")
    for token_id in tokens:
        token_str = tokenizer.decode([token_id])
        print(f"  id {token_id:>4}: {token_str!r}")


def main() -> None:
    device = choose_device()
    print(f"Using device: {device}")

    tokenizer = load_tokenizer()
    show_tokenization(tokenizer)

    config = ChatbotConfig(
        vocab_size=len(tokenizer),
        max_seq_len=160,
        hidden_size=384,
        num_layers=8,
        num_heads=6,
        ff_multiplier=4.5,
        dropout=0.1,
        attention_dropout=0.1,
        device=str(device),
    )

    model = build_model(config)
    describe_model(model, config)

    dataset = ReasoningChatDataset(SAMPLE_DIALOGUES, tokenizer, max_length=config.max_seq_len)
    batches = list(
        batch_iterator(
            dataset,
            batch_size=2,
            pad_token_id=tokenizer.pad_token_id,
            device=device,
        )
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    run_dummy_training(model, optimizer, batches, epochs=1)

    prompt = "USER: hello, can you explain how to stay organized?"
    reply = generate_reply(model, tokenizer, prompt, max_new_tokens=60)
    print("Sample generation (untrained weights, so expect gibberish):")
    print(reply)

    print("Model built! You can now train it with your data using the train_step() function.")


if __name__ == "__main__":
    main()
