import torch

from fnc.fnc_core.config import FNCConfig
from fnc.generator.generator_model import FractalGenerator


def test_generator_output_shape():
    cfg = FNCConfig()
    generator = FractalGenerator(cfg.generator)
    seed = torch.tensor([[1]])
    coords = torch.zeros(1, cfg.generator.coord_embed_dim)
    context = {"lod": 2, "shape": (8, 8)}
    result = generator(seed, coords, context)
    assert "weights" in result
    assert result["weights"].shape == (1, 8, 8)
    assert result["aux"]["lod_used"] == 2
