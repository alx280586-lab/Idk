import torch

from fnc.fnc_core.caching import SimpleCache
from fnc.fnc_core.precision import PrecisionPolicy
from fnc.fnc_core.seeds import SeedRegistry
from fnc.fnc_core.tensor_coords import CoordinateEncoder
from fnc.inference.static_generator import StaticWeightGenerator
from fnc.worker.fnc_param_proxy import FNCParamProxy


def test_static_generator_materialises_registered_block():
    spec = ("attn_q_proj", 0, 0, 4, 4)
    weight = torch.tensor(list(range(16)), dtype=torch.float32).view(4, 4)
    generator = StaticWeightGenerator({spec: weight})
    cache = SimpleCache(max_entries=2)
    precision = PrecisionPolicy(default_bits=16)
    seeds = SeedRegistry(0)
    coord_encoder = CoordinateEncoder(embed_dim=generator.coord_embed_dim)
    proxy = FNCParamProxy(spec, seeds.seed_for(spec), coord_encoder, generator, cache, precision)
    materialised = proxy.materialize()
    assert materialised.shape == (4, 4)
    assert torch.allclose(materialised, weight, atol=1e-3)
