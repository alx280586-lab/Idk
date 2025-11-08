# Mini Reasoning Chatbot Tutorial

This repository now contains a multi-file, beginner-friendly walkthrough for
building a reasoning-aware GPT-style chatbot with PyTorch. The code is split
into the `mini_chatbot/` package and a runnable `train_chatbot.py` script so you
can inspect each subsystem independently.

## Layout

- `mini_chatbot/config.py` – configuration dataclass with safety checks.
- `mini_chatbot/model_components.py` – rotary attention and gated feed-forward blocks.
- `mini_chatbot/model.py` – high-level `MiniReasoningGPT` transformer definition.
- `mini_chatbot/tokenization.py` – tokenizer setup with chat-specific tokens.
- `mini_chatbot/datasets.py` – reasoning-focused dialogue samples and batching utilities.
- `mini_chatbot/training.py` – commented dummy training loop and helper functions.
- `mini_chatbot/generation.py` – top-k sampling utilities for reply generation.
- `train_chatbot.py` – orchestrates everything for a quick demo run.

Run the main script with:

```bash
python train_chatbot.py
```

It will construct the model, print configuration details, run a dummy training
epoch, and sample a reply (expect gibberish until you fine-tune on real data).
