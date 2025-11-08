# ChatWeaver-4B Blueprint

This repository scaffolds **ChatWeaver-4B**, a 4-billion-parameter GPT-style
chat model optimized for consumer GPUs. It contains modular code for tokenizer
training, model definition, full mixed-precision training, inference, and
quantization.

## Components

- `model.py` – Transformer decoder definition with rotary embeddings, grouped
  query attention, Flash Attention support, and SwiGLU feed-forward layers.
- `tokenizer_train.py` – SentencePiece tokenizer trainer for text and Alpaca-
  style JSONL corpora.
- `train.py` – Mixed-precision training loop with gradient checkpointing,
  AdamW + cosine schedule, distributed hooks, evaluation metrics, and optional
  LoRA adapters.
- `quickstart.py` – Guided launcher that trains a tokenizer, creates configs, and
  starts training with sensible defaults for non-experts.
- `chat.py` – Interactive inference script that loads trained checkpoints.
- `config.yaml` – Example configuration covering model, optimization, and
  training hyperparameters.
- `QUANTIZATION.md` – Instructions for 4-bit quantization and GGUF export.
- `TRAINING_GUIDE.md` – Step-by-step walkthrough covering installation,
  quickstart usage, manual configuration, and troubleshooting.

## Quickstart

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   If PyTorch is missing, choose a wheel for your platform, e.g.:

   ```bash
   # CPU-only
   pip install torch --index-url https://download.pytorch.org/whl/cpu

   # NVIDIA GPUs (CUDA 12.1)
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```

   See [TRAINING_GUIDE.md](TRAINING_GUIDE.md#install-pytorch) for additional wheel
   links and troubleshooting tips.

2. **Verify your environment**

   ```bash
   python quickstart.py --doctor
   ```

   This prints the detected Python, PyTorch, and SentencePiece versions and points
   out anything missing before you launch training.

3. **Run the guided training wizard** (uses the bundled toy dataset by default):

   ```bash
   python quickstart.py --model-preset mini --max-steps 50
   ```

   This command trains a small tokenizer, launches a lightweight model, and
   saves checkpoints to `quickstart_runs/checkpoints/`. Switch to
   `--model-preset full` when you are ready for the 4B configuration and have
   enough compute.

4. **Chat with a checkpoint**

   ```bash
   python chat.py --checkpoint checkpoints/chatweaver-4b/last.pt \
                  --tokenizer tokenizer/chatweaver-spm.model
   ```

Need more detail? See [TRAINING_GUIDE.md](TRAINING_GUIDE.md) for comprehensive
instructions, including manual YAML editing, LoRA fine-tuning, and monitoring
metrics.

For quantization instructions, see [QUANTIZATION.md](QUANTIZATION.md).
