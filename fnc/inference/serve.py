"""HTTP serving entry point."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict

import torch

from fnc.fnc_core.config import FNCConfig
from fnc.fnc_core.caching import SimpleCache
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.seeds import SeedRegistry
from fnc.generator.generator_model import FractalGenerator
from fnc.worker.worker_skeleton import FNCWorker, WorkerConfig


class FNCRequestHandler(BaseHTTPRequestHandler):
    cfg = FNCConfig()
    generator = FractalGenerator(cfg.generator)
    cache = SimpleCache()
    precision = PrecisionPolicy(cfg.generator.quant_policy.get("default_bits", 8))
    seeds = SeedRegistry(cfg.training.seed)
    worker = FNCWorker(
        WorkerConfig(
            d_model=cfg.model.d_model,
            n_layers=cfg.model.n_layers,
            n_heads=cfg.model.n_heads,
            vocab_size=cfg.model.vocab_size,
            max_seq_len=cfg.model.max_seq_len,
            mlp_ratio=cfg.model.mlp_ratio,
        ),
        generator,
        cache,
        precision,
        seeds,
    )

    def do_POST(self) -> None:  # pragma: no cover - network I/O
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length)) if length else {}
        tokens = torch.randint(0, self.cfg.model.vocab_size, (1, self.cfg.model.max_seq_len))
        logits = self.worker(tokens)
        response: Dict[str, float] = {"logits_mean": float(logits.mean().item())}
        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover - network I/O
    server = HTTPServer((host, port), FNCRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":  # pragma: no cover
    main()
