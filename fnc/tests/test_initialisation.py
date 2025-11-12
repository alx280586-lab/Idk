from __future__ import annotations

from fnc.fnc_core.config import FNCConfig
from fnc.generator.checkpoints import load_generator_checkpoint
from fnc.training.init_model import initialise_model_bundle


def test_initialise_model_bundle(tmp_path) -> None:
    cfg = FNCConfig()
    cfg.model.d_model = 32
    cfg.model.n_layers = 2
    cfg.model.n_heads = 4
    cfg.model.vocab_size = 256
    cfg.model.max_seq_len = 16
    cfg.generator.latent_dim = 64
    cfg.generator.coord_embed_dim = 32
    cfg.generator.modulation_dim = 32
    cfg.generator.num_lod = 3

    output_dir = tmp_path / "bundle"
    checkpoint_path = initialise_model_bundle(cfg, output_dir)

    state = load_generator_checkpoint(checkpoint_path)
    assert "config" in state
    assert state["config"]["model"]["d_model"] == cfg.model.d_model
    assert "metadata" in state and state["metadata"]["status"] == "initialised"
    assert "footprint" in state["metadata"]
    assert state["metadata"]["footprint"]["virtual_params"] >= state["metadata"]["footprint"]["total_params"]
    assert "seeds" in state and len(state["seeds"]) > 0
    assert "precision" in state and state["precision"]["default_bits"] == cfg.generator.quant_policy.get("default_bits", 8)
