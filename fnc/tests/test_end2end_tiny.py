import torch

from fnc.fnc_core.caching import SimpleCache
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.seeds import SeedRegistry
from fnc.fnc_core.config import FNCConfig
from fnc.generator.generator_model import FractalGenerator
from fnc.worker.worker_skeleton import FNCWorker, WorkerConfig


def test_worker_forward_runs():
    cfg = FNCConfig()
    cfg.model.d_model = 16
    cfg.model.n_heads = 2
    cfg.model.vocab_size = 32
    generator = FractalGenerator(cfg.generator)
    cache = SimpleCache(max_entries=8)
    precision = PrecisionPolicy(cfg.generator.quant_policy.get("default_bits", 8))
    seeds = SeedRegistry(cfg.training.seed)
    worker_cfg = WorkerConfig(
        d_model=cfg.model.d_model,
        n_layers=1,
        n_heads=cfg.model.n_heads,
        vocab_size=cfg.model.vocab_size,
        max_seq_len=8,
    )
    worker = FNCWorker(worker_cfg, generator, cache, precision, seeds)
    tokens = torch.randint(0, worker_cfg.vocab_size, (1, worker_cfg.max_seq_len))
    logits = worker(tokens)
    assert logits.shape[0] == 1
