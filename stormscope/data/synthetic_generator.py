"""Synthetic radar data generator used by the simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

from .radar_volume import RadarVolume


@dataclass
class StormCellState:
    """Track intrinsic properties of a synthetic storm cell."""

    id: int
    center: np.ndarray
    velocity: np.ndarray
    intensity: float
    rotation: float
    hail_potential: float
    rainfall_rate: float

    def advance(self, dt: float, domain: Tuple[float, float]) -> None:
        """Advance the storm position and evolve its properties."""

        domain_array = np.array(domain)
        self.center = (self.center + self.velocity * dt) % domain_array
        decay = 0.98 ** dt
        self.intensity = max(20.0, self.intensity * decay)
        self.rotation = max(0.0, self.rotation * decay)
        self.hail_potential = max(0.0, self.hail_potential * decay)
        self.rainfall_rate = max(0.0, self.rainfall_rate * decay)


class SyntheticRadarGenerator:
    """Produce synthetic radar volumes that mimic severe storm environments."""

    def __init__(
        self,
        grid_shape: Tuple[int, int, int] = (8, 200, 200),
        domain_size: Tuple[float, float] = (200.0, 200.0),
        seed: int | None = None,
    ) -> None:
        self.grid_shape = grid_shape
        self.domain_size = domain_size
        self.rng = np.random.default_rng(seed)
        self.elevation_angles = np.linspace(0.5, 15.0, grid_shape[0])
        self.cells: Dict[int, StormCellState] = {}
        self._next_id = 1

    def step(self, time_seconds: float) -> RadarVolume:
        """Generate a new radar volume for the provided simulation time."""

        self._maintain_cells(time_seconds)
        z = np.zeros(self.grid_shape, dtype=float)
        v = np.zeros_like(z)
        zdr = np.zeros_like(z)
        cc = np.ones_like(z)
        kdp = np.zeros_like(z)
        sw = np.zeros_like(z)

        ranges_y = np.linspace(0, self.domain_size[1], self.grid_shape[1])
        ranges_x = np.linspace(0, self.domain_size[0], self.grid_shape[2])
        yy, xx = np.meshgrid(ranges_y, ranges_x, indexing="ij")

        for cell in self.cells.values():
            dx = xx - cell.center[0]
            dy = yy - cell.center[1]
            distance = np.sqrt(dx**2 + dy**2)
            footprint = np.exp(-(distance**2) / (2 * 10.0**2))
            column = np.exp(-np.linspace(0, 1.5, self.grid_shape[0]))[:, None, None]
            cell_reflectivity = cell.intensity * footprint * column
            z += cell_reflectivity
            rotation_pattern = (dx * cell.velocity[1] - dy * cell.velocity[0]) / 10.0
            v += rotation_pattern * column * 3.0 + cell.velocity[0]
            zdr += (1.5 + 0.5 * self.rng.standard_normal()) * footprint * column
            cc -= 0.05 * footprint * column * (cell.rotation > 25)
            kdp += (cell.rainfall_rate / 20.0) * footprint * column
            sw += np.abs(rotation_pattern) * column * 0.5

        noise = self.rng.normal(scale=1.5, size=self.grid_shape)
        z = np.clip(z + noise, -5, 80)
        v += self.rng.normal(scale=1.0, size=self.grid_shape)
        zdr = np.clip(zdr + self.rng.normal(scale=0.2, size=self.grid_shape), -2.0, 5.0)
        cc = np.clip(cc, 0.2, 1.0)
        kdp = np.clip(kdp, -2.0, 10.0)
        sw = np.clip(sw + self.rng.normal(scale=0.5, size=self.grid_shape), 0.0, 12.0)

        metadata = {"time": time_seconds, "storm_count": len(self.cells)}
        return RadarVolume(
            fields={
                "reflectivity": z,
                "velocity": v,
                "zdr": zdr,
                "cc": cc,
                "kdp": kdp,
                "spectrum_width": sw,
            },
            elevation_angles=self.elevation_angles,
            metadata=metadata,
        )

    def _maintain_cells(self, time_seconds: float) -> None:
        """Update existing storms and spawn new ones as needed."""

        for cell in list(self.cells.values()):
            cell.advance(1.0, self.domain_size)
            if cell.intensity < 25 and self.rng.random() < 0.05:
                del self.cells[cell.id]

        while len(self.cells) < 4:
            self._spawn_cell(time_seconds)

    def _spawn_cell(self, time_seconds: float) -> None:
        center = self.rng.uniform([0, 0], self.domain_size)
        speed = self.rng.uniform(5, 25)
        heading = self.rng.uniform(0, 2 * np.pi)
        velocity = np.array([np.cos(heading), np.sin(heading)]) * speed / 60.0
        intensity = self.rng.uniform(45, 70)
        rotation = self.rng.uniform(10, 60)
        hail_potential = self.rng.uniform(0, 1)
        rainfall_rate = self.rng.uniform(20, 100)

        cell = StormCellState(
            id=self._next_id,
            center=center,
            velocity=velocity,
            intensity=intensity,
            rotation=rotation,
            hail_potential=hail_potential,
            rainfall_rate=rainfall_rate,
        )
        self._next_id += 1
        self.cells[cell.id] = cell
