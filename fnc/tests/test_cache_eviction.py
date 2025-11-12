import torch

from fnc.fnc_core.caching import SimpleCache


def test_simple_cache_eviction():
    cache = SimpleCache(max_entries=2, max_bytes=10)
    cache.insert("a", torch.zeros(1), cost=1)
    cache.insert("b", torch.zeros(1), cost=1)
    cache.insert("c", torch.zeros(1), cost=1)
    assert cache.lookup("a") is None
    assert cache.lookup("b") is not None or cache.lookup("c") is not None
    info = cache.info()
    assert "bytes" in info and info["bytes"] <= 10
