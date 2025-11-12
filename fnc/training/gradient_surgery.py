"""Gradient surgery stubs."""
from __future__ import annotations

from typing import Iterable

import torch


def clip_global_norm(parameters: Iterable[torch.nn.Parameter], max_norm: float) -> None:
    torch.nn.utils.clip_grad_norm_(parameters, max_norm)


__all__ = ["clip_global_norm"]
