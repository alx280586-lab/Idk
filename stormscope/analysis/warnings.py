"""Warning and alert generation logic."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Iterable, List, Sequence

import numpy as np


class WarningType(Enum):
    SEVERE_THUNDERSTORM = auto()
    TORNADO = auto()
    TORNADO_EMERGENCY = auto()
    FLASH_FLOOD = auto()


@dataclass
class WarningPolygon:
    warning_type: WarningType
    vertices: np.ndarray
    valid_until: float
    motion_vector: np.ndarray
    metadata: Dict[str, object] = field(default_factory=dict)

    def contains(self, point: np.ndarray) -> bool:
        x, y = point
        verts = self.vertices
        inside = False
        j = len(verts) - 1
        for i in range(len(verts)):
            xi, yi = verts[i]
            xj, yj = verts[j]
            intersect = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / (yj - yi + 1e-6) + xi
            )
            if intersect:
                inside = not inside
            j = i
        return inside


@dataclass
class StormAttributes:
    id: int
    position: np.ndarray
    motion: np.ndarray
    max_reflectivity: float
    max_rotation: float
    mesh: float
    rainfall_rate: float
    debris_detected: bool
    area_km2: float
    major_axis_km: float
    minor_axis_km: float
    age_seconds: float


@dataclass
class StormAlertHistory:
    """Maintain smoothed severity metrics for a tracked storm."""

    last_update: float = 0.0
    tornado_score: float = 0.0
    hail_score: float = 0.0
    flood_score: float = 0.0
    severe_score: float = 0.0
    debris_confidence: float = 0.0

    def update(self, storm: StormAttributes, time_seconds: float) -> None:
        dt = 0.0 if self.last_update == 0.0 else max(time_seconds - self.last_update, 0.0)
        self.last_update = time_seconds

        def smooth(value: float, contribution: float, tau: float) -> float:
            if dt <= 0.0:
                return contribution
            weight = float(np.exp(-dt / tau))
            return value * weight + contribution * (1.0 - weight)

        rotation_term = max(0.0, (storm.max_rotation - 32.0) / 18.0)
        debris_term = 1.2 if storm.debris_detected else 0.0
        hail_support = max(0.0, storm.mesh - 1.25) * 0.4
        tornado_component = rotation_term + hail_support + debris_term

        hail_component = max(0.0, storm.mesh - 0.75)
        hail_component += max(0.0, storm.max_reflectivity - 60.0) / 15.0

        flood_component = max(0.0, storm.rainfall_rate - 4.5) / 3.0
        flood_component += max(0.0, storm.area_km2 - 150.0) / 200.0

        wind_component = max(0.0, storm.max_rotation - 28.0) / 25.0
        size_component = max(0.0, storm.major_axis_km - 18.0) / 20.0
        severe_component = max(hail_component * 0.8, wind_component + size_component)

        self.tornado_score = smooth(self.tornado_score, tornado_component, tau=240.0)
        self.hail_score = smooth(self.hail_score, hail_component, tau=180.0)
        self.flood_score = smooth(self.flood_score, flood_component, tau=420.0)
        self.severe_score = smooth(self.severe_score, severe_component, tau=210.0)
        self.debris_confidence = smooth(
            self.debris_confidence,
            1.0 if storm.debris_detected else 0.0,
            tau=120.0,
        )

class WarningEngine:
    """Generate alert polygons from storm attributes."""

    def __init__(self, domain_size: np.ndarray):
        self.domain_size = np.array(domain_size, dtype=float)
        self.active: Dict[int, WarningPolygon] = {}
        self._history: Dict[int, StormAlertHistory] = {}

    def update(self, time_seconds: float, storms: Sequence[StormAttributes]) -> List[WarningPolygon]:
        active: Dict[int, WarningPolygon] = {
            sid: poly
            for sid, poly in self.active.items()
            if poly.valid_until > time_seconds
        }
        issued: List[WarningPolygon] = []

        for storm in storms:
            history = self._history.get(storm.id)
            if history is None:
                history = StormAlertHistory()
            history.update(storm, time_seconds)
            self._history[storm.id] = history

            polygon = self._build_polygon(time_seconds, storm, history)
            if polygon is None:
                continue

            existing = active.get(storm.id)
            if existing:
                if self._priority(existing.warning_type) > self._priority(polygon.warning_type):
                    continue
                if existing.warning_type == polygon.warning_type:
                    blended_vertices = self._blend_vertices(existing.vertices, polygon.vertices)
                    existing.vertices = blended_vertices
                    existing.valid_until = max(existing.valid_until, polygon.valid_until)
                    existing.metadata.update(polygon.metadata)
                    active[storm.id] = existing
                    continue

            active[storm.id] = polygon
            if existing is None or existing.warning_type != polygon.warning_type:
                issued.append(polygon)

        stale_ids = [
            sid
            for sid, history in self._history.items()
            if time_seconds - history.last_update > 900.0 and sid not in active
        ]
        for sid in stale_ids:
            self._history.pop(sid, None)

        self.active = active
        return issued

    def _build_polygon(
        self,
        time_seconds: float,
        storm: StormAttributes,
        history: StormAlertHistory,
    ) -> WarningPolygon | None:
        warning_type: WarningType | None = None
        metadata: Dict[str, object] = {}

        maturity_minutes = storm.age_seconds / 60.0
        tornado_score = history.tornado_score
        hail_score = history.hail_score
        severe_score = history.severe_score
        flood_score = history.flood_score

        if (
            tornado_score >= 1.6
            and history.debris_confidence >= 0.6
            and storm.max_rotation > 55.0
            and storm.area_km2 >= 60.0
        ):
            warning_type = WarningType.TORNADO_EMERGENCY
            metadata["hazard"] = "Tornado emergency"
            metadata["source"] = "Radar confirmed debris"
        elif (
            tornado_score >= 1.0 and maturity_minutes >= 3.0
        ) or (storm.debris_detected and storm.max_rotation > 50.0):
            warning_type = WarningType.TORNADO
            metadata["hazard"] = "Tornado"
            metadata["source"] = "Radar indicated rotation"
        elif (
            hail_score >= 0.85 or severe_score >= 0.9 or tornado_score >= 0.7
        ) and (maturity_minutes >= 4.0 or hail_score >= 1.2):
            warning_type = WarningType.SEVERE_THUNDERSTORM
            hazard_parts = []
            if hail_score >= 0.85:
                hazard_parts.append(f"Hail {storm.mesh:.1f}\"")
            if severe_score >= 0.9:
                hazard_parts.append("Damaging winds")
            if tornado_score >= 0.7:
                hazard_parts.append("Rotation noted")
            metadata["hazard"] = ", ".join(hazard_parts) or "Severe hail/wind"
            metadata["source"] = "Radar indicated"
        elif flood_score >= 1.1 and maturity_minutes >= 8.0:
            warning_type = WarningType.FLASH_FLOOD
            metadata["hazard"] = "Flash flooding"
            metadata["source"] = "Radar rainfall estimates"

        if warning_type is None:
            return None

        duration = {
            WarningType.TORNADO_EMERGENCY: 1800,
            WarningType.TORNADO: 1800,
            WarningType.SEVERE_THUNDERSTORM: 3600,
            WarningType.FLASH_FLOOD: 5400,
        }[warning_type]

        corridor = self._motion_corridor(storm, duration)
        polygon = WarningPolygon(
            warning_type=warning_type,
            vertices=corridor,
            valid_until=time_seconds + duration,
            motion_vector=storm.motion,
            metadata={
                **metadata,
                "storm_id": storm.id,
                "confidence": round(self._confidence(warning_type, history), 2),
                "storm_age_min": round(maturity_minutes, 1),
            },
        )
        return polygon

    def _motion_corridor(self, storm: StormAttributes, duration: float) -> np.ndarray:
        minutes = duration / 60.0
        motion = storm.motion
        position = storm.position
        speed = float(np.linalg.norm(motion))
        half_width = max(10.0, 0.6 * max(storm.major_axis_km, storm.minor_axis_km) + 6.0)
        if speed < 0.5:
            half_size_x = max(half_width, np.sqrt(storm.area_km2) / 2.0 + 6.0)
            square = np.array(
                [
                    position + [-half_size_x, -half_width],
                    position + [half_size_x, -half_width],
                    position + [half_size_x, half_width],
                    position + [-half_size_x, half_width],
                ]
            )
            return np.clip(square, [0, 0], self.domain_size)

        direction = motion / speed
        perpendicular = np.array([-direction[1], direction[0]])
        start = position
        end = position + motion * minutes
        corridor = np.array(
            [
                start + perpendicular * half_width,
                start - perpendicular * half_width,
                end - perpendicular * half_width,
                end + perpendicular * half_width,
            ]
        )
        return np.clip(corridor, [0, 0], self.domain_size)

    def _blend_vertices(self, current: np.ndarray, new: np.ndarray) -> np.ndarray:
        if current.shape != new.shape:
            return new
        weight = 0.3
        return current * (1 - weight) + new * weight

    def _priority(self, warning_type: WarningType) -> int:
        order = {
            WarningType.FLASH_FLOOD: 0,
            WarningType.SEVERE_THUNDERSTORM: 1,
            WarningType.TORNADO: 2,
            WarningType.TORNADO_EMERGENCY: 3,
        }
        return order.get(warning_type, 0)

    def _confidence(self, warning_type: WarningType, history: StormAlertHistory) -> float:
        if warning_type == WarningType.TORNADO_EMERGENCY:
            score = history.tornado_score + history.debris_confidence
            return max(0.0, min(score / 2.4, 1.0))
        if warning_type == WarningType.TORNADO:
            return max(0.0, min((history.tornado_score + history.debris_confidence) / 2.0, 1.0))
        if warning_type == WarningType.SEVERE_THUNDERSTORM:
            combined = max(history.hail_score, history.severe_score)
            return max(0.0, min(combined / 1.4, 1.0))
        if warning_type == WarningType.FLASH_FLOOD:
            return max(0.0, min(history.flood_score / 1.6, 1.0))
        return 0.0
