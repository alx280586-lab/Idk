from fnc.fnc_core.seeds import SeedRegistry


def test_seed_registry_determinism():
    registry = SeedRegistry(master_seed=123)
    spec = ("attn_q_proj", 0, 0, 0, 0)
    first = registry.seed_for(spec)
    second = registry.seed_for(spec)
    assert first.item() == second.item()
