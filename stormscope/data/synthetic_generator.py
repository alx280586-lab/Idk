"""Synthetic radar data generator used by the simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from .radar_volume import RadarVolume


@dataclass
class StormCellState:
    """Track intrinsic properties of a synthetic storm cell."""

    id: int
    center: np.ndarray
    velocity: np.ndarray
    peak_intensity: float
    peak_rotation: float
    peak_hail: float
    peak_rainfall: float
    lifespan: float
    age: float = 0.0

    def advance(self, dt: float, domain: Tuple[float, float], rng: np.random.Generator) -> None:
        """Advance the storm position and evolve its properties smoothly."""

        domain_array = np.array(domain)
        minutes = dt / 60.0
        jitter = rng.normal(scale=0.05, size=2)
        self.center = (self.center + (self.velocity + jitter) * minutes) % domain_array
        self.age = min(self.age + dt, self.lifespan)

        normalized_age = np.clip(self.age / self.lifespan, 0.0, 1.0)
        growth_phase = np.clip(normalized_age / 0.65, 0.0, 1.0) ** 1.6
        decay_phase = np.clip((normalized_age - 0.55) / 0.45, 0.0, 1.0)

        def smooth_profile(peak: float, base: float) -> float:
            value = base + (peak - base) * growth_phase
            return float(value * (1.0 - 0.65 * decay_phase))

        self._current_intensity = smooth_profile(self.peak_intensity, base=8.0)
        self._current_rotation = smooth_profile(self.peak_rotation, base=4.0)
        self._current_hail = smooth_profile(self.peak_hail, base=0.1)
        self._current_rainfall = smooth_profile(self.peak_rainfall, base=8.0)

    @property
    def intensity(self) -> float:
        return float(getattr(self, "_current_intensity", self.peak_intensity))

    @property
    def rotation(self) -> float:
        return float(getattr(self, "_current_rotation", self.peak_rotation))

    @property
    def hail_potential(self) -> float:
        return float(getattr(self, "_current_hail", self.peak_hail))

    @property
    def rainfall_rate(self) -> float:
        return float(getattr(self, "_current_rainfall", self.peak_rainfall))


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
        self._last_time = None

        kernel_size = 9
        sigma = 2.0
        ax = np.linspace(-(kernel_size // 2), kernel_size // 2, kernel_size)
        kernel = np.exp(-(ax[:, None] ** 2 + ax[None, :] ** 2) / (2 * sigma**2))
        self._smoothing_kernel = kernel / kernel.sum()

    def step(self, time_seconds: float) -> RadarVolume:
        """Generate a new radar volume for the provided simulation time."""

        dt = 60.0 if self._last_time is None else max(time_seconds - self._last_time, 1.0)
        self._last_time = time_seconds

        self._maintain_cells(dt, time_seconds)
        z = np.zeros(self.grid_shape, dtype=float)
        v = np.zeros_like(z)
        zdr = np.zeros_like(z)
        cc = np.ones_like(z)
        kdp = np.zeros_like(z)
        sw = np.zeros_like(z)

        ranges_y = np.linspace(0, self.domain_size[1], self.grid_shape[1])
        ranges_x = np.linspace(0, self.domain_size[0], self.grid_shape[2])
        yy, xx = np.meshgrid(ranges_y, ranges_x, indexing="ij")

        for cell in list(self.cells.values()):
            cell.advance(dt, self.domain_size, self.rng)
            if cell.age >= cell.lifespan:
                del self.cells[cell.id]
                continue

            dx = xx - cell.center[0]
            dy = yy - cell.center[1]
            distance = np.sqrt(dx**2 + dy**2)
            footprint = np.exp(-(distance**2) / (2 * 12.0**2))
            column = np.exp(-np.linspace(0, 1.5, self.grid_shape[0]))[:, None, None]
            cell_reflectivity = cell.intensity * footprint * column
            z += cell_reflectivity
            rotation_pattern = (dx * cell.velocity[1] - dy * cell.velocity[0]) / 18.0
            v += rotation_pattern * column * 2.0 + cell.velocity[0]
            zdr += (1.0 + 0.25 * self.rng.standard_normal()) * footprint * column
            cc -= 0.05 * footprint * column * (cell.rotation > 45)
            kdp += (cell.rainfall_rate / 25.0) * footprint * column
            sw += np.abs(rotation_pattern) * column * 0.5

        z = self._smooth_volume(z + self.rng.normal(scale=0.8, size=self.grid_shape))
        v = self._smooth_volume(v + self.rng.normal(scale=0.6, size=self.grid_shape))
        zdr = self._smooth_volume(
            np.clip(zdr + self.rng.normal(scale=0.15, size=self.grid_shape), -2.0, 5.0)
        )
        cc = np.clip(cc, 0.2, 1.0)
        kdp = np.clip(self._smooth_volume(kdp), -1.0, 8.0)
        sw = np.clip(self._smooth_volume(sw + self.rng.normal(scale=0.3, size=self.grid_shape)), 0.0, 10.0)

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

    def _maintain_cells(self, dt: float, time_seconds: float) -> None:
        """Update existing storms and spawn new ones as needed."""

        # ensure a modest number of simultaneous storms for readability
        while len(self.cells) < 1:
            self._spawn_cell(time_seconds)
        if len(self.cells) < 3 and self.rng.random() < dt / 1500.0:
            self._spawn_cell(time_seconds)

    def _smooth_volume(self, data: np.ndarray) -> np.ndarray:
        radius = self._smoothing_kernel.shape[0] // 2
        padded = np.pad(data, ((0, 0), (radius, radius), (radius, radius)), mode="reflect")
        windows = sliding_window_view(padded, self._smoothing_kernel.shape, axis=(1, 2))
        smoothed = np.tensordot(windows, self._smoothing_kernel, axes=((3, 4), (0, 1)))
        return smoothed

    def _spawn_cell(self, time_seconds: float) -> None:
        center = self.rng.uniform([0, 0], self.domain_size)
        speed_ms = self.rng.uniform(10, 30)
        heading = self.rng.uniform(0, 2 * np.pi)
        velocity = np.array([np.cos(heading), np.sin(heading)]) * (speed_ms * 0.06)
        peak_intensity = self.rng.uniform(48, 68)
        peak_rotation = self.rng.uniform(18, 45)
        peak_hail = self.rng.uniform(0.6, 1.8)
        peak_rain = self.rng.uniform(35, 85)
        lifespan = self.rng.uniform(2100, 4200)

        cell = StormCellState(
            id=self._next_id,
            center=center,
            velocity=velocity,
            peak_intensity=peak_intensity,
            peak_rotation=peak_rotation,
            peak_hail=peak_hail,
            peak_rainfall=peak_rain,
            lifespan=lifespan,
        )
        self._next_id += 1
        self.cells[cell.id] = cell
