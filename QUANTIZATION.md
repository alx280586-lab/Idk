# ChatWeaver-4B Quantization and GGUF Export

This guide outlines a reference workflow for producing 4-bit ChatWeaver-4B
artifacts that run well on consumer GPUs.

## Prerequisites

- A trained ChatWeaver-4B checkpoint saved by `train.py` (e.g., `outputs/last.pt`).
- `bitsandbytes>=0.41`, `transformers>=4.40`, and `accelerate` if you want to run
  4-bit inference in PyTorch.
- [`llama.cpp`](https://github.com/ggerganov/llama.cpp) for GGUF export.

## 4-bit Quantization with bitsandbytes

1. **Convert the checkpoint to Hugging Face format**

   ```bash
   python tools/convert_to_hf.py \
     --checkpoint outputs/last.pt \
     --tokenizer tokenizer/chatweaver-spm.model \
     --out-dir hf-chatweaver-4b
   ```

   The conversion helper (see template below) maps state dict keys to the
   expected Hugging Face layout and writes `config.json`, `pytorch_model.bin`,
   and tokenizer assets.

2. **Load in 4-bit**

   ```python
   from transformers import AutoModelForCausalLM, AutoTokenizer

   model = AutoModelForCausalLM.from_pretrained(
       "hf-chatweaver-4b",
       device_map="auto",
       load_in_4bit=True,
       bnb_4bit_compute_dtype=torch.bfloat16,
       bnb_4bit_quant_type="nf4",
   )
   tokenizer = AutoTokenizer.from_pretrained("hf-chatweaver-4b")
   ```

3. **Run inference**

   Use `model.generate` as usual. ChatWeaver's architecture is compatible with
   Flash Attention 2 if your GPU supports it.

## GGUF Export

1. **Create a GGML binary**

   ```bash
   python tools/convert_to_gguf.py \
     --checkpoint outputs/last.pt \
     --tokenizer tokenizer/chatweaver-spm.model \
     --out ggml/chatweaver-4b.gguf
   ```

   The converter needs to reformat weights and rotary embeddings. Follow the
   structure used by llama.cpp: map keys to `layers.*.attention.wq.weight`, etc.

2. **Quantize with llama.cpp**

   ```bash
   ./quantize ggml/chatweaver-4b.gguf ggml/chatweaver-4b-q4_0.gguf Q4_0
   ```

   Alternatives such as `Q4_K_M` provide higher accuracy at a modest size cost.

3. **Run locally**

   ```bash
   ./main -m ggml/chatweaver-4b-q4_0.gguf -n 256 -p "Hello!"
   ```

## Template: PyTorch → Hugging Face Conversion Helper

```python
import argparse
import json
import shutil
from pathlib import Path

import torch
from model import ChatWeaverModel


def convert(checkpoint: str, tokenizer_path: str, out_dir: str) -> None:
    model = ChatWeaverModel.from_checkpoint(checkpoint, map_location="cpu")
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_path / "pytorch_model.bin")
    with open(out_path / "config.json", "w", encoding="utf-8") as fp:
        json.dump(model.config.__dict__, fp, indent=2)
    shutil.copy(tokenizer_path, out_path / "tokenizer.model")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    convert(args.checkpoint, args.tokenizer, args.out_dir)
```

Adjust the mapping logic to match any downstream tooling (e.g., PEFT adapters or
special tokens). The template is intentionally lightweight.
