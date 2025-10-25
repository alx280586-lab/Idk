"""Data structures representing synthetic radar volumes and fields."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping

import numpy as np


RADAR_FIELDS = (
    "reflectivity",
    "velocity",
    "zdr",
    "cc",
    "kdp",
    "spectrum_width",
)


@dataclass(frozen=True)
class RadarVolume:
    """Container for a single radar volume scan.

    Parameters
    ----------
    fields:
        Mapping between radar product names and 3-D arrays with shape
        ``(nz, ny, nx)`` describing the radar grid.
    elevation_angles:
        The elevation angle in degrees for each vertical level.
    metadata:
        Additional metadata describing the volume, e.g. timestamp,
        radar ID, or simulated truth flags.
    """

    fields: Mapping[str, np.ndarray]
    elevation_angles: np.ndarray
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, array in self.fields.items():
            if array.ndim != 3:
                raise ValueError(f"Radar field '{name}' must be 3-D, got {array.ndim}D")
        shapes = {array.shape for array in self.fields.values()}
        if len(shapes) > 1:
            raise ValueError(f"All radar fields must share the same grid, got {shapes}")
        if self.elevation_angles.ndim != 1:
            raise ValueError("Elevation angles must be a 1-D array")
        if self.elevation_angles.size != next(iter(self.fields.values())).shape[0]:
            raise ValueError(
                "Elevation angle count must match the vertical dimension of the fields",
            )

    @property
    def grid_shape(self) -> Iterable[int]:
        """Return the ``(nz, ny, nx)`` shape of the radar grid."""

        return next(iter(self.fields.values())).shape

    def field(self, name: str) -> np.ndarray:
        """Return a read-only view of a radar product array."""

        if name not in self.fields:
            raise KeyError(f"Radar field '{name}' is not available in this volume")
        return self.fields[name]
