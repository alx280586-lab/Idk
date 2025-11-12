# Fractal Neural Compression (FNC)

Fractal Neural Compression (FNC) is a modular research codebase that trains a
compact *generator* network to procedurally synthesise the weights of a much
larger *worker* transformer. Instead of storing billions of parameters, the
worker requests deterministic blocks on demand; the generator recreates them
from a seed, a coordinate tuple, and runtime context. This design enables
massive effective model sizes while keeping the in-memory footprint small enough
for commodity hardware.

The repository ships ready-to-run tooling for a **10-trillion-parameter
equivalent** worker: a configuration whose base transformer holds hundreds of
billions of logical weights, amplified by 24 levels of fractal detail. Because
the generator re-materialises each block deterministically, only the active few
megabytes live in memory at any given time, allowing experimentation on a
single workstation or high-end laptop.

The repository contains runnable training and inference entry points together
with tests that exercise determinism, caching, precision policies, and a tiny
end-to-end forward pass. Once the dependencies are installed, you can prepare a
toy dataset, train the generator, and run inference using the provided CLI
wrappers.

## System overview

* **Generator (`fnc/generator/`)** – A compact neural network composed of
  spectral field decoders, fractal noise primitives, and FiLM-like modulation.
  It accepts `(seed, coordinates, context)` triples and emits weight tensors plus
  auxiliary statistics. Quantisation policies are learned through a light-weight
  head that supports straight-through gradients during training.
* **Worker (`fnc/worker/`)** – A decoder-only transformer skeleton whose
  parameters are replaced by `FNCParamProxy` instances. Each proxy materialises
  its block lazily, funnels the result through the precision controller, and
  caches the tensor for reuse within the step.
* **Runtime (`fnc/runtime/`)** – Cache, paging, and device-map helpers that make
  it practical to stream weight blocks on laptops. The current prototype ships a
  deterministic LRU cache with pinning semantics; extending it with GPU paging
  policies is an expected next milestone.
* **Training (`fnc/training/`)** – Meta-training utilities that backpropagate
  through the worker into the generator. The pipeline module assembles the
  system, drives the curriculum (bootstrap → progressive LoD → distillation), and
  persists checkpoints. Stage-specific logic lives in dedicated modules so that
  experiments can swap in alternative schedulers.
* **Inference (`fnc/inference/`)** – CLI and server entry points that load a
  saved bundle, generate tokens autoregressively, and report cache statistics
  together with latency.

The remaining packages (`fnc_core`, `experiments`, `configs`, `scripts`,
`tests`) provide shared utilities, ablation scaffolding, configuration presets,
automation helpers, and verification harnesses.

## Repository layout

```
fnc/
  fnc_core/          # configuration, deterministic seeds, coordinates, precision, caching
  generator/         # fractal generator model, primitives, quantisers, checkpoints
  worker/            # transformer skeleton with lazy parameter proxies
  runtime/           # cache/device hooks for streaming procedural weights
  training/          # meta-training loops, CLI, and pipeline orchestration
  inference/         # text generation CLI and lightweight HTTP server
  experiments/       # ablation helpers and sweep templates
  tests/             # determinism, caching, precision, and tiny end-to-end tests
  scripts/           # shell wrappers for data prep, training, evaluation, export
  configs/           # OmegaConf-compatible presets for common hardware tiers
```

## Quickstart

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Prepare a seed corpus

The repository ships a tiny byte-level corpus for smoke testing. Copy it to a
workspace directory (or replace it with your own data) using the helper script:

```bash
./fnc/scripts/prepare_data.sh data/tiny_corpus.txt
```

Update `configs/base.yaml` (or the hardware-specific presets) if you want to
point at a custom dataset path.

### 3. Train the generator

The `fnc.training.cli` Typer application exposes the three-stage curriculum:

1. **Bootstrap (Stage 1)** – bring the generator online against a small worker
   skeleton.
2. **Progressive detail (Stage 2)** – unlock additional levels of detail and
   finer quantisation policies.
3. **Self-distillation (Stage 3)** – stabilise newly unlocked detail levels by
   distilling from the best checkpoint so far.

For a quick bootstrap run:

```bash
./fnc/scripts/train_small.sh --config configs/base.yaml --steps 50 --checkpoint-dir runs/stage1
```

To continue with progressive detail and distillation:

```bash
./fnc/scripts/train_progressive.sh --config configs/progressive_levels.yaml --steps 50 --checkpoint-dir runs/stage2
python -m fnc.training.cli distill --config configs/base.yaml --steps 50 --checkpoint-dir runs/stage3
```

The orchestration pipeline clears caches between steps, ensuring each pass sees
freshly generated blocks so gradients propagate cleanly into the generator.

### 4. Inspect the virtual parameter count

FNC includes a footprint inspector that reports both the physical parameter
count and the LoD-amplified virtual capacity. This is particularly useful for
the 10T-equivalent build described below:

```bash
python -m fnc.training.cli estimate --config configs/ten_trillion.yaml
```

Use `--lod` to inspect hypothetical unlock levels without editing the config.

### 5. Run inference

Use the saved bundle with the text generation CLI. The script prints the sampled
output together with cache hit rates and latency:

```bash
./fnc/scripts/eval_perplexity.sh --bundle runs/stage1 --prompt "Fractal compression" --max-new-tokens 20
```

The bundle loader automatically restores the generator weights, precision
policy, and seed registry captured during training. Override configuration
fields with `--config` if you need to run on different hardware at inference
time.

### 6. Export checkpoints

To copy the trained generator checkpoint into a portable location:

```bash
./fnc/scripts/export_checkpoint.sh runs/stage1/generator.pt artifacts/generator.pt
```

## Testing

Run the full unit suite (ensuring the repo root is on `PYTHONPATH`) to verify
deterministic seeding, cache semantics, and the tiny worker forward pass:

```bash
pytest fnc/tests -q
```

## Configuration notes

* `fnc/fnc_core/config.py` defines dataclasses for model, generator, runtime,
  training, and logging settings. The loader understands YAML (via OmegaConf)
  and JSON payloads and feeds them into the training/inference stack.
* The training pipeline resolves datasets automatically: if `data.dataset_path`
  exists it will be used, otherwise the synthetic byte-level corpus keeps the
  plumbing exercised.
* Precision policies support per-block overrides and use a straight-through fake
  quantiser during training so gradients still flow through the proxies.

## Architecture deep dive

1. **Deterministic seeds and coordinates** – The seed registry hands out a
   stable integer per block specification. `CoordinateEncoder` maps block tuples
   `(block_type, layer, head, row, col)` into dense vectors that feed the
   generator. The combination uniquely determines each weight block, while the
   per-element spectral grid reconstructed inside the generator ensures smooth
   spatial variation within each tensor.
2. **Fractal generator** – Seeds are embedded into a latent, modulated by block
   coordinates, and decoded through spectral fields enriched with fractal noise.
   The decoder builds harmonic feature grids at multiple levels of detail and
   projects them onto the latent basis, yielding arbitrarily large tensors with
   consistent detail structure. Auxiliary statistics (e.g., virtual parameter
   count, level-of-detail usage) accompany each block for logging or
   regularisation.
3. **Lazy worker** – Parameter proxies call the generator on cache misses and
   store detached copies in the runtime cache. Training re-materialises the
   tensors each step to ensure gradients stay current, while inference benefits
   from hit rates. Cache entries track their effective byte footprint so runtime
   budgets can be enforced.
4. **Training loop** – `fnc.training.pipeline` orchestrates the curriculum. It
   builds the bundle, iterates over byte-token batches, applies optional
   regularisers, and checkpoints generator/optimizer state. The progressive
   scheduler unlocks new levels of detail according to `training.lod_milestones`.
5. **Inference** – The CLI loads the saved bundle, samples autoregressively using
   byte-level tokens, and reports cache statistics so you can reason about
   streaming efficiency on the target hardware.

## Understanding the 10T-equivalent build

The preset in `configs/ten_trillion.yaml` combines a wide, deep worker with 24
levels of fractal detail. The base transformer weighs in at ~4.6×10¹¹ physical
parameters; every unlocked level of detail adds another copy of those degrees of
freedom. Unlocking all 24 levels yields **1.1×10¹³ virtual parameters** while
never storing more than the currently active blocks in memory.

* Run a dry estimation to confirm the footprint:

  ```bash
  python -m fnc.training.cli estimate --config configs/ten_trillion.yaml
  ```

* Execute the staged curriculum (with intentionally tiny step counts for smoke
  tests) via:

  ```bash
  ./fnc/scripts/train_10t.sh STAGE1_STEPS=5 PROGRESSIVE_STEPS=5 DISTILL_STEPS=5
  ```

  Increase the step counts as resources allow. Each stage resumes from the
  previous checkpoints, progressively unlocking more detail and adjusting the
  learned quantisation policy.

* During training and inference the runtime cache bounds its footprint using the
  configured GPU/CPU budgets. Only the blocks referenced by the current layer
  and prefetch window are materialised; everything else can be regenerated from
  the seed table on demand. The cache statistics reported in logs and inference
  output help diagnose whether the streaming pipeline fits within the target
  hardware envelope.

The preset is intentionally aggressive to illustrate the procedural weight
generation philosophy. In practice, begin with a smaller worker, verify that
loss and cache metrics behave as expected, and then scale depth and levels of
detail.

## Status & roadmap

The current implementation is a research prototype. Key areas left intentionally
open include learned tokenisers, high-fidelity fractal primitives, paged GPU
runtime kernels, and large-scale training curricula. See
`experiments/ablations.py` for ideas on comparing noise sources, quantisation
policies, and cache strategies.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for the
full text.
