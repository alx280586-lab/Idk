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


class WarningEngine:
    """Generate alert polygons from storm attributes."""

    def __init__(self, domain_size: np.ndarray):
        self.domain_size = domain_size
        self.active: Dict[int, WarningPolygon] = {}

    def update(self, time_seconds: float, storms: Sequence[StormAttributes]) -> List[WarningPolygon]:
        active: Dict[int, WarningPolygon] = {
            sid: poly
            for sid, poly in self.active.items()
            if poly.valid_until > time_seconds
        }
        issued: List[WarningPolygon] = []

        for storm in storms:
            polygon = self._build_polygon(time_seconds, storm)
            if polygon is None:
                continue
            active[storm.id] = polygon
            issued.append(polygon)

        self.active = active
        return issued

    def _build_polygon(self, time_seconds: float, storm: StormAttributes) -> WarningPolygon | None:
        warning_type: WarningType | None = None
        metadata: Dict[str, object] = {}

        if storm.max_rotation > 45 and storm.debris_detected:
            warning_type = WarningType.TORNADO_EMERGENCY
            metadata["hazard"] = "Catastrophic tornado damage likely"
            metadata["source"] = "Radar confirmed debris"
        elif storm.max_rotation > 35:
            warning_type = WarningType.TORNADO
            metadata["hazard"] = "Tornado"
            metadata["source"] = "Radar indicated rotation"
        elif storm.mesh >= 1.0 or storm.max_reflectivity > 60:
            warning_type = WarningType.SEVERE_THUNDERSTORM
            hazard_parts = []
            if storm.mesh >= 1.0:
                hazard_parts.append(f"Hail {storm.mesh:.1f}\"")
            if storm.max_reflectivity > 60:
                hazard_parts.append("60+ dBZ core")
            metadata["hazard"] = ", ".join(hazard_parts) or "Severe hail/wind"
            metadata["source"] = "Radar indicated"
        elif storm.rainfall_rate > 4.0:
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

        corridor = self._motion_corridor(storm.position, storm.motion, duration)
        polygon = WarningPolygon(
            warning_type=warning_type,
            vertices=corridor,
            valid_until=time_seconds + duration,
            motion_vector=storm.motion,
            metadata={**metadata, "storm_id": storm.id},
        )
        return polygon

    def _motion_corridor(self, position: np.ndarray, motion: np.ndarray, duration: float) -> np.ndarray:
        lead_time = np.linspace(0, duration, num=4)
        trajectory = position[None, :] + motion[None, :] * lead_time[:, None] / 60.0
        offsets = np.array([[4, 4], [-4, 4], [-4, -4], [4, -4]])
        polygon = []
        for point in trajectory:
            for offset in offsets:
                candidate = np.clip(point + offset, [0, 0], self.domain_size)
                polygon.append(candidate)
        return np.array(polygon)
