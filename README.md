# ChatWeaver-4B Blueprint

This repository scaffolds ChatWeaver-4B, a 4-billion-parameter GPT-style chat
model optimized for consumer GPUs.

## Components

- `model.py` – Transformer decoder definition with rotary embeddings, grouped
  query attention, Flash Attention support, and SwiGLU feed-forward layers.
- `tokenizer_train.py` – SentencePiece tokenizer trainer for text and Alpaca-
  style JSONL corpora.
- `train.py` – Mixed-precision training loop with gradient checkpointing,
  AdamW + cosine schedule, distributed hooks, evaluation metrics, and optional
  LoRA adapters.
- `chat.py` – Interactive inference script that loads trained checkpoints.
- `config.yaml` – Example configuration covering model, optimization, and
  training hyperparameters.
- `QUANTIZATION.md` – Instructions for 4-bit quantization and GGUF export.

## Quickstart

1. **Train the tokenizer**

   ```bash
   python tokenizer_train.py data/corpus.jsonl --work-dir tokenizer
   ```

2. **Launch pretraining or fine-tuning**

   ```bash
   python train.py --config config.yaml
   ```

   Need a sanity check without massive hardware? Run the built-in CPU demo to
   exercise the full pipeline on a toy dataset:

   ```bash
   python train.py --demo
   ```

3. **Chat with a checkpoint**

   ```bash
   python chat.py --checkpoint checkpoints/chatweaver-4b/last.pt \
                  --tokenizer tokenizer/chatweaver-spm.model
   ```

For quantization instructions, see [QUANTIZATION.md](QUANTIZATION.md).
