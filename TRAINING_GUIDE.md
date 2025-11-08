# ChatWeaver-4B Training Guide

This guide walks you through training ChatWeaver from scratch or running a
small-scale dry run without needing to edit code. Every step assumes you are in
this repository's root directory.

## 1. Install Dependencies

1. Create a Python 3.10+ environment (virtualenv, conda, etc.).
2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

   > **Tip:** For GPU training, install the matching CUDA build of PyTorch from
   > [pytorch.org](https://pytorch.org/get-started/locally/).

## 2. Pick a Training Path

You have two options depending on your goal and hardware.

### Option A – Quickstart Wizard (minimal effort)

Run the guided launcher that handles tokenizer training, config creation, and
kicks off training in one command:

```bash
python quickstart.py \
  --model-preset mini \
  --max-steps 50
```

What happens automatically:

1. `examples/sample_dialog.jsonl` is used as both the tokenizer and training
   corpus (override with `--data` if you have your own files).
2. A SentencePiece tokenizer is trained under `quickstart_runs/tokenizer/`.
3. A lightweight model config (12 layers, 1B-class) is constructed.
4. Training artifacts are saved under `quickstart_runs/checkpoints/`.

You can scale up by switching `--model-preset base` or `--model-preset full` and
adjusting `--batch-size`, `--micro-batch-size`, and `--max-steps` to fit your
hardware. Use `--val-data path.jsonl` to add an evaluation split, and add
`--lora-rank 8` to fine-tune with LoRA adapters instead of full weights.

### Option B – Manual Control (advanced users)

1. **Prepare data.** Collect plain text (`.txt`) or Alpaca-style JSONL files.
2. **Train the tokenizer.**

   ```bash
   python tokenizer_train.py data/corpus.jsonl --work-dir tokenizer
   ```

3. **Edit `config.yaml`.** Update the paths under `training.train_data`,
   `training.tokenizer_path`, and `training.output_dir` to match your setup.
4. **Launch training.**

   ```bash
   python train.py --config config.yaml
   ```

   Add `--demo` to run the CPU-only sanity check.

## 3. Understand the Key Settings

- **Batch size vs. micro-batch size:** Use a small `micro_batch_size` that fits
  in memory and let the trainer accumulate gradients to reach your desired
  `batch_size`.
- **Precision:** `bf16` and `fp16` reduce memory use but require GPUs with
  native support. Set `precision=fp32` on CPUs or older GPUs.
- **Gradient checkpointing:** Enabled by default in the `full` preset to squeeze
  large models into consumer GPUs.
- **LoRA fine-tuning:** Supply `--lora-rank` in `quickstart.py` or set
  `training.lora` in the YAML config to update only lightweight adapter layers.

## 4. Monitor Training

- Checkpoints and logs are stored under your chosen `output_dir`.
- The trainer prints loss, perplexity, BLEU, and helpfulness metrics every
  `log_interval` steps. Adjust intervals to control frequency.
- Resume an interrupted run via `training.resume_from` in the YAML or by
  rerunning `quickstart.py --resume-from <checkpoint>`.

## 5. After Training

1. **Run inference:**

   ```bash
   python chat.py --checkpoint <path-to-checkpoint> --tokenizer <path-to-tokenizer>
   ```

2. **Quantize:** Follow the step-by-step instructions in `QUANTIZATION.md` to
   produce 4-bit GGUF or GPTQ builds for local deployment.

3. **Fine-tune further:** Use LoRA (`--lora-rank`) or resume from checkpoints to
   continue training with new data.

## 6. Troubleshooting Tips

- If PyTorch reports CUDA errors, confirm you installed the correct CUDA wheels
  and that `nvidia-smi` lists your GPU.
- Reduce `--model-preset` or `--context-length` if you hit OOM errors.
- For tiny experiments on CPU, keep `--max-steps` under 50 and use the
  `mini` preset.
- Ensure JSONL files have `instruction`, `input`, and `output` keys; otherwise
  set `--jsonl-text-field text` to read a specific field.

With these steps, you can go from raw text to a trained ChatWeaver checkpoint
with minimal manual editing.
