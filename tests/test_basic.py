from nfce.semantic_field.field import SemanticField, FieldState
import torch


def test_field_forward():
    field = SemanticField()
    state = FieldState(grid=torch.zeros(1, 8, 32), time=0.0)
    next_state = field(state)
    assert next_state.grid.shape == state.grid.shape
