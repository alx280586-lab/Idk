"""Identify storms and derive attributes from radar volumes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from ..data.products import RadarProductComputer
from .warnings import StormAttributes


@dataclass
class StormDetectionConfig:
    reflectivity_threshold: float = 40.0
    min_pixels: int = 40
    debris_cc_threshold: float = 0.85


class StormDetector:
    def __init__(self, config: StormDetectionConfig | None = None):
        self.config = config or StormDetectionConfig()
        self._next_id = 1

    def detect(self, volume) -> List[StormAttributes]:
        products = RadarProductComputer(volume)
        refl_ppi = products.ppi("reflectivity", elevation_index=0).data
        rotation = products.normalized_rotation()
        mesh = products.maximum_estimated_hail_size()
        rainfall = products.rainfall_rate()
        cc = volume.field("cc").min(axis=0)

        mask = refl_ppi >= self.config.reflectivity_threshold
        labeled = self._label_regions(mask)
        storms: List[StormAttributes] = []
        for label in np.unique(labeled):
            if label == 0:
                continue
            indices = np.argwhere(labeled == label)
            if indices.shape[0] < self.config.min_pixels:
                continue
            y_mean, x_mean = indices.mean(axis=0)
            max_refl = float(refl_ppi[labeled == label].max())
            max_rotation = float(rotation[labeled == label].max())
            max_mesh = float(mesh[labeled == label].max())
            max_rain = float(rainfall[labeled == label].max())
            debris = bool((cc[labeled == label] < self.config.debris_cc_threshold).any())
            motion = self._estimate_motion(label, indices)
            storm = StormAttributes(
                id=self._next_id,
                position=np.array([x_mean, y_mean], dtype=float),
                motion=motion,
                max_reflectivity=max_refl,
                max_rotation=max_rotation,
                mesh=max_mesh,
                rainfall_rate=max_rain,
                debris_detected=debris,
            )
            self._next_id += 1
            storms.append(storm)
        return storms

    def _label_regions(self, mask: np.ndarray) -> np.ndarray:
        labeled = np.zeros(mask.shape, dtype=int)
        current_label = 0
        visited = np.zeros_like(mask, dtype=bool)
        for y in range(mask.shape[0]):
            for x in range(mask.shape[1]):
                if not mask[y, x] or visited[y, x]:
                    continue
                current_label += 1
                stack = [(y, x)]
                while stack:
                    cy, cx = stack.pop()
                    if visited[cy, cx]:
                        continue
                    visited[cy, cx] = True
                    labeled[cy, cx] = current_label
                    for ny in range(max(0, cy - 1), min(mask.shape[0], cy + 2)):
                        for nx in range(max(0, cx - 1), min(mask.shape[1], cx + 2)):
                            if mask[ny, nx] and not visited[ny, nx]:
                                stack.append((ny, nx))
        return labeled

    def _estimate_motion(self, label: int, indices: np.ndarray) -> np.ndarray:
        if indices.size == 0:
            return np.zeros(2)
        vy = np.gradient(indices[:, 0]).mean() if indices.shape[0] > 1 else 0.0
        vx = np.gradient(indices[:, 1]).mean() if indices.shape[0] > 1 else 0.0
        return np.array([vx, vy], dtype=float)
