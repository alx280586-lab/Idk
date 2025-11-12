import torch

from fnc.fnc_core.precision import PrecisionPolicy


def test_precision_quantize_reduces_range():
    tensor = torch.linspace(-1, 1, steps=10)
    policy = PrecisionPolicy(default_bits=4)
    quantized = policy.quantize(tensor, "test")
    assert quantized.abs().max() <= tensor.abs().max()
