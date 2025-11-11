# Fractal Neural Compression (FNC)

Fractal Neural Compression (FNC) is a modular research codebase that trains a
compact *generator* network to procedurally synthesise the weights of a much
larger *worker* transformer. Instead of storing billions of parameters, the
worker requests deterministic blocks on demand; the generator recreates them
from a seed, a coordinate tuple, and runtime context. This design enables
massive effective model sizes while keeping the in-memory footprint small enough
for commodity hardware.

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

The `fnc.training.cli` Typer application exposes the curriculum stages. For a
quick bootstrap run:

```bash
./fnc/scripts/train_small.sh --config configs/base.yaml --steps 50 --checkpoint-dir runs/stage1
```

This command builds the generator/worker bundle, streams batches from the seed
corpus, and persists the resulting checkpoint artefacts into `runs/stage1/`. For
progressive detail or distillation follow-ups:

```bash
./fnc/scripts/train_progressive.sh --config configs/progressive_levels.yaml --steps 50 --checkpoint-dir runs/stage2
python -m fnc.training.cli distill --config configs/base.yaml --steps 50 --checkpoint-dir runs/stage3
```

### 4. Run inference

Use the saved bundle with the text generation CLI. The script prints the sampled
output together with cache hit rates and latency:

```bash
./fnc/scripts/eval_perplexity.sh --bundle runs/stage1 --prompt "Fractal compression" --max-new-tokens 20
```

The bundle loader automatically restores the generator weights, precision
policy, and seed registry captured during training. Override configuration
fields with `--config` if you need to run on different hardware at inference
time.

### 5. Export checkpoints

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
   generator. The combination uniquely determines each weight block.
2. **Fractal generator** – Seeds are embedded into a latent, modulated by block
   coordinates, and decoded through spectral fields enriched with fractal noise.
   Auxiliary statistics (e.g., level-of-detail usage) accompany the generated
   tensor for logging or regularisation.
3. **Lazy worker** – Parameter proxies call the generator on cache misses and
   store detached copies in the runtime cache. Training re-materialises the
   tensors each step to ensure gradients stay current, while inference benefits
   from hit rates.
4. **Training loop** – `fnc.training.pipeline` orchestrates the curriculum. It
   builds the bundle, iterates over byte-token batches, applies optional
   regularisers, and checkpoints generator/optimizer state.
5. **Inference** – The CLI loads the saved bundle, samples autoregressively using
   byte-level tokens, and reports cache statistics so you can reason about
   streaming efficiency on the target hardware.

## Status & roadmap

The current implementation is a research prototype. Key areas left intentionally
open include learned tokenisers, high-fidelity fractal primitives, paged GPU
runtime kernels, and large-scale training curricula. See
`experiments/ablations.py` for ideas on comparing noise sources, quantisation
policies, and cache strategies.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for the
full text.
