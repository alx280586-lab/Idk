"""Identify storms and derive attributes from radar volumes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np

from ..data.products import RadarProductComputer
from .warnings import StormAttributes


@dataclass
class StormDetectionConfig:
    reflectivity_threshold: float = 40.0
    min_pixels: int = 40
    debris_cc_threshold: float = 0.85
    match_distance: float = 25.0
    memory_seconds: float = 360.0


@dataclass
class _TrackedStorm:
    id: int
    position: np.ndarray
    last_seen: float
    motion: np.ndarray = field(default_factory=lambda: np.zeros(2))


class StormDetector:
    def __init__(self, config: StormDetectionConfig | None = None):
        self.config = config or StormDetectionConfig()
        self._next_id = 1
        self._tracked: Dict[int, _TrackedStorm] = {}

    def detect(self, volume, time_seconds: float) -> List[StormAttributes]:
        products = RadarProductComputer(volume)
        refl_ppi = products.ppi("reflectivity", elevation_index=0).data
        rotation = products.normalized_rotation()
        mesh = products.maximum_estimated_hail_size()
        rainfall = products.rainfall_rate()
        cc = volume.field("cc").min(axis=0)

        mask = refl_ppi >= self.config.reflectivity_threshold
        labeled = self._label_regions(mask)
        candidates: List[StormAttributes] = []
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
            candidate = StormAttributes(
                id=-1,
                position=np.array([x_mean, y_mean], dtype=float),
                motion=np.zeros(2),
                max_reflectivity=max_refl,
                max_rotation=max_rotation,
                mesh=max_mesh,
                rainfall_rate=max_rain,
                debris_detected=debris,
            )
            candidates.append(candidate)

        storms = self._match_tracks(candidates, time_seconds)
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

    def _match_tracks(self, detections: List[StormAttributes], time_seconds: float) -> List[StormAttributes]:
        updated: Dict[int, _TrackedStorm] = {}
        matched_storms: List[StormAttributes] = []
        available_ids = set(self._tracked.keys())

        for detection in detections:
            best_id = None
            best_distance = None
            for tracked_id in list(available_ids):
                tracked = self._tracked[tracked_id]
                distance = float(np.linalg.norm(detection.position - tracked.position))
                if distance > self.config.match_distance:
                    continue
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_id = tracked_id

            if best_id is not None:
                available_ids.remove(best_id)
                tracked = self._tracked[best_id]
                dt_minutes = max((time_seconds - tracked.last_seen) / 60.0, 1e-6)
                motion = (detection.position - tracked.position) / dt_minutes
                detection = StormAttributes(
                    id=best_id,
                    position=detection.position,
                    motion=motion,
                    max_reflectivity=detection.max_reflectivity,
                    max_rotation=detection.max_rotation,
                    mesh=detection.mesh,
                    rainfall_rate=detection.rainfall_rate,
                    debris_detected=detection.debris_detected,
                )
            else:
                detection = StormAttributes(
                    id=self._next_id,
                    position=detection.position,
                    motion=np.zeros(2),
                    max_reflectivity=detection.max_reflectivity,
                    max_rotation=detection.max_rotation,
                    mesh=detection.mesh,
                    rainfall_rate=detection.rainfall_rate,
                    debris_detected=detection.debris_detected,
                )
                self._next_id += 1

            updated[detection.id] = _TrackedStorm(
                id=detection.id,
                position=detection.position,
                last_seen=time_seconds,
                motion=detection.motion,
            )
            matched_storms.append(detection)

        # carry forward recently-missed detections to maintain continuity
        for tracked_id in available_ids:
            tracked = self._tracked[tracked_id]
            if time_seconds - tracked.last_seen <= self.config.memory_seconds:
                updated[tracked_id] = tracked

        self._tracked = updated
        return matched_storms
