# Fractal Neural Compression (FNC)

Fractal Neural Compression (FNC) is an experimental research codebase exploring
procedural weight generation for large language models. The repository provides
an extensible scaffold for meta-training a compact generator network that
synthesises the parameters of a much larger worker transformer on demand. The
project emphasises determinism, streaming-friendly runtime primitives, and
progressive levels of detail that can fit within commodity hardware budgets.

## Repository layout

```
fnc/
  fnc_core/          # deterministic seeds, coordinate systems, caching & precision
  generator/         # fractal generator model and supporting building blocks
  worker/            # transformer skeleton with lazy parameter proxies
  runtime/           # cache, paging, and device-mapping utilities
  training/          # meta-training loops and curriculum stages
  inference/         # CLI and serving entry points
  experiments/       # ablation helpers and sweep definitions
  tests/             # unit tests validating determinism and caching
  scripts/           # helper shell scripts for data prep and training flows
  configs/           # OmegaConf-compatible configuration presets
```

Each module is implemented with research-friendly stubs that document the
expected behaviour and highlight open problems. Contributors are encouraged to
replace the placeholders with production-ready implementations.

## Getting started

1. Create a Python 3.11+ environment and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the test suite to verify the installation:

   ```bash
   PYTHONPATH=. pytest fnc/tests -q
   ```

3. Explore the `configs/` directory for hardware-specific presets and use the
   `scripts/train_small.sh` script as a starting point for Stage 1 bootstrap
   experiments.

## Documentation

- `fnc/fnc_core/config.py` documents the hierarchical configuration objects.
- `fnc/generator/` describes the fractal primitives and modulation mechanisms.
- `fnc/runtime/` covers cache policies, paging, and prefetching strategies.
- `fnc/training/` explains the progressive curriculum and meta-optimisation
  loops.
- `fnc/inference/` exposes CLI and HTTP interfaces for running inference on
  commodity hardware.

## Status & roadmap

This repository provides scaffolding rather than a production-quality FNC
implementation. Key research tasks—such as efficient fractal synthesis kernels,
robust quantisation policies, and large-scale training recipes—are intentionally
left as TODOs. See `experiments/ablations.py` for suggested investigations.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for
additional details.
