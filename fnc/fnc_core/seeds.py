"""Seed registry ensuring deterministic block generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

import torch


@dataclass
class SeedRegistry:
    """Tracks deterministic seeds for each block specification."""

    master_seed: int
    _table: Dict[Tuple, int] = field(default_factory=dict)

    def seed_for(self, block_spec: Tuple) -> torch.Tensor:
        """Return a torch tensor seed for *block_spec*, creating one if needed."""
        if block_spec not in self._table:
            derived = hash((self.master_seed, block_spec)) % (2**31)
            self._table[block_spec] = derived
        seed_value = self._table[block_spec]
        return torch.tensor(seed_value, dtype=torch.int64)

    def as_dict(self) -> Dict[str, int]:
        """Expose a serialisable mapping."""
        return {str(key): value for key, value in self._table.items()}


__all__ = ["SeedRegistry"]
