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
    min_pixels: int = 60
    debris_cc_threshold: float = 0.85
    match_distance: float = 30.0
    memory_seconds: float = 360.0


@dataclass
class _TrackedStorm:
    id: int
    position: np.ndarray
    last_seen: float
    motion: np.ndarray = field(default_factory=lambda: np.zeros(2))
    age_seconds: float = 0.0


class StormDetector:
    def __init__(
        self,
        config: StormDetectionConfig | None = None,
        domain_size: tuple[float, float] = (200.0, 200.0),
    ):
        self.config = config or StormDetectionConfig()
        self.domain_size = np.array(domain_size, dtype=float)
        self._next_id = 1
        self._tracked: Dict[int, _TrackedStorm] = {}

    def detect(self, volume, time_seconds: float) -> List[StormAttributes]:
        products = RadarProductComputer(volume)
        refl_ppi = products.ppi("reflectivity", elevation_index=0).data
        rotation = products.normalized_rotation()
        mesh = products.maximum_estimated_hail_size()
        rainfall = products.rainfall_rate()
        cc = volume.field("cc").min(axis=0)

        pixel_scale_x = self.domain_size[0] / refl_ppi.shape[1]
        pixel_scale_y = self.domain_size[1] / refl_ppi.shape[0]

        mask = refl_ppi >= self.config.reflectivity_threshold
        labeled = self._label_regions(mask)
        candidates: List[StormAttributes] = []
        for label in np.unique(labeled):
            if label == 0:
                continue
            indices = np.argwhere(labeled == label)
            if indices.shape[0] < self.config.min_pixels:
                continue
            region_mask = labeled == label
            max_refl = float(refl_ppi[region_mask].max())
            max_rotation = float(rotation[region_mask].max())
            max_mesh = float(mesh[region_mask].max())
            max_rain = float(rainfall[region_mask].max())
            debris = bool((cc[region_mask] < self.config.debris_cc_threshold).any())

            coords = indices.astype(float)
            x_coords = (coords[:, 1] + 0.5) * pixel_scale_x
            y_coords = (coords[:, 0] + 0.5) * pixel_scale_y
            position = np.array([x_coords.mean(), y_coords.mean()], dtype=float)
            area_km2 = float(indices.shape[0] * pixel_scale_x * pixel_scale_y)

            if coords.shape[0] > 2:
                centered = np.column_stack((x_coords, y_coords))
                cov = np.cov(centered, rowvar=False)
                eigvals = np.sort(np.clip(np.linalg.eigvalsh(cov), a_min=0.0, a_max=None))
                major_axis = float(2.0 * np.sqrt(eigvals[-1])) if eigvals.size else 0.0
                minor_axis = float(2.0 * np.sqrt(eigvals[0])) if eigvals.size else 0.0
            else:
                base_size = float(np.sqrt(pixel_scale_x * pixel_scale_y))
                major_axis = minor_axis = base_size

            candidate = StormAttributes(
                id=-1,
                position=position,
                motion=np.zeros(2),
                max_reflectivity=max_refl,
                max_rotation=max_rotation,
                mesh=max_mesh,
                rainfall_rate=max_rain,
                debris_detected=debris,
                area_km2=area_km2,
                major_axis_km=major_axis,
                minor_axis_km=minor_axis,
                age_seconds=0.0,
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
                dt_minutes = max((time_seconds - tracked.last_seen) / 60.0, 1e-3)
                predicted = tracked.position + tracked.motion * dt_minutes
                distance = float(np.linalg.norm(detection.position - predicted))
                if distance > self.config.match_distance:
                    continue
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_id = tracked_id

            if best_id is not None:
                available_ids.remove(best_id)
                tracked = self._tracked[best_id]
                dt_seconds = max(time_seconds - tracked.last_seen, 1.0)
                dt_minutes = dt_seconds / 60.0
                raw_motion = (detection.position - tracked.position) / dt_minutes
                motion = 0.6 * tracked.motion + 0.4 * raw_motion
                age_seconds = tracked.age_seconds + dt_seconds
                detection = StormAttributes(
                    id=best_id,
                    position=detection.position,
                    motion=motion,
                    max_reflectivity=detection.max_reflectivity,
                    max_rotation=detection.max_rotation,
                    mesh=detection.mesh,
                    rainfall_rate=detection.rainfall_rate,
                    debris_detected=detection.debris_detected,
                    area_km2=detection.area_km2,
                    major_axis_km=detection.major_axis_km,
                    minor_axis_km=detection.minor_axis_km,
                    age_seconds=age_seconds,
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
                    area_km2=detection.area_km2,
                    major_axis_km=detection.major_axis_km,
                    minor_axis_km=detection.minor_axis_km,
                    age_seconds=detection.age_seconds,
                )
                self._next_id += 1

            updated[detection.id] = _TrackedStorm(
                id=detection.id,
                position=detection.position,
                last_seen=time_seconds,
                motion=detection.motion,
                age_seconds=age_seconds if best_id is not None else detection.age_seconds,
            )
            matched_storms.append(detection)

        # carry forward recently-missed detections to maintain continuity
        for tracked_id in available_ids:
            tracked = self._tracked[tracked_id]
            if time_seconds - tracked.last_seen <= self.config.memory_seconds:
                updated[tracked_id] = tracked

        self._tracked = updated
        return matched_storms
