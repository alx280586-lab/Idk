"""Radar product derivations used for visualization and decision making."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .radar_volume import RadarVolume


@dataclass(frozen=True)
class PlanPositionIndicator:
    """Planar representation of a radar field."""

    field_name: str
    elevation_index: int | None
    data: np.ndarray
    units: str
    description: str


class RadarProductComputer:
    """Derive 2-D displays and storm metrics from a :class:`RadarVolume`."""

    def __init__(self, volume: RadarVolume):
        self.volume = volume

    def ppi(self, field_name: str, elevation_index: int | None = 0) -> PlanPositionIndicator:
        field = self.volume.field(field_name)
        if elevation_index is None:
            projection = field.max(axis=0)
            description = f"{field_name.title()} (max composite)"
        else:
            if elevation_index >= field.shape[0]:
                raise IndexError("Elevation index out of range")
            projection = field[elevation_index]
            description = (
                f"{field_name.title()} @ {self.volume.elevation_angles[elevation_index]:.1f}°"
            )
        units = {
            "reflectivity": "dBZ",
            "velocity": "m/s",
            "zdr": "dB",
            "cc": "",
            "kdp": "°/km",
            "spectrum_width": "m/s",
        }.get(field_name, "")
        return PlanPositionIndicator(field_name, elevation_index, projection, units, description)

    def echo_tops(self, threshold: float = 18.0) -> np.ndarray:
        field = self.volume.field("reflectivity")
        mask = field >= threshold
        heights = mask.argmax(axis=0)
        heights[~mask.max(axis=0)] = 0
        return heights * 0.5

    def vertically_integrated_liquid(self) -> np.ndarray:
        refl = np.clip(self.volume.field("reflectivity"), 0.0, None)
        z_linear = 10 ** (refl / 10.0)
        dz = 0.5
        vil = np.sum(z_linear * dz, axis=0)
        return vil / 1000.0

    def maximum_estimated_hail_size(self) -> np.ndarray:
        refl = self.volume.field("reflectivity")
        zdr = self.volume.field("zdr")
        hail_core = np.maximum(refl - 50.0, 0)
        hail_factor = np.clip(1.5 - np.abs(zdr - 0.2), 0.0, 2.0)
        mesh = hail_core.max(axis=0) * hail_factor.max(axis=0) / 10.0
        return mesh

    def normalized_rotation(self) -> np.ndarray:
        velocity = self.volume.field("velocity")
        dv_dy = np.gradient(velocity, axis=1)
        dv_dx = np.gradient(velocity, axis=2)
        shear = np.hypot(dv_dy, dv_dx)
        return shear.max(axis=0)

    def rainfall_rate(self) -> np.ndarray:
        kdp = np.clip(self.volume.field("kdp"), 0, None)
        return 15.0 * kdp.max(axis=0)
