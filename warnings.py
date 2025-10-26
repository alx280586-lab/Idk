"""Warning generation engine for the radar simulator.

This module intentionally shares its filename with the Python stdlib module.
To avoid breaking imports that expect :mod:`warnings`, we embed the stdlib
implementation under the hood and re-export common helpers such as
:func:`warn`.
"""
from __future__ import annotations

import os
import sysconfig
import types

# Bootstrap a copy of the standard-library warnings helpers so third-party
# modules importing ``warnings`` still find familiar functions.  Without this
# dance the simulator would steal the module name and the stdlib would sulk.
_stdlib_path = os.path.join(sysconfig.get_path("stdlib"), "warnings.py")
_stdlib_module = types.ModuleType("_stdlib_warnings")
with open(_stdlib_path, "r", encoding="utf-8") as fh:
    code = compile(fh.read(), _stdlib_path, "exec")
exec(code, _stdlib_module.__dict__)
warn = _stdlib_module.warn
simplefilter = _stdlib_module.simplefilter
filterwarnings = _stdlib_module.filterwarnings

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple
from datetime import datetime, timedelta
from PyQt6.QtGui import QColor
import numpy as np

from detectors import Detection
from storm_generator import StormCell


WARNING_COLORS = {
    "Tornado Warning": QColor(220, 40, 40, 160),
    "PDS Tornado Warning": QColor(180, 0, 0, 170),
    "Tornado Emergency": QColor(120, 0, 0, 200),
    "Severe Thunderstorm Warning": QColor(255, 165, 0, 150),
    "PDS Severe Thunderstorm Warning": QColor(255, 120, 0, 170),
    "Flash Flood Warning": QColor(30, 180, 30, 160),
    "PDS Flash Flood Warning": QColor(20, 120, 20, 180),
    "Severe Hail Warning": QColor(160, 60, 200, 160),
    "Damaging Wind Warning": QColor(200, 200, 0, 160),
    "Special Marine Warning": QColor(0, 150, 255, 150),
    "Winter Storm Warning": QColor(120, 120, 255, 160),
    "Snow Squall Warning": QColor(180, 180, 255, 160),
    "Red Flag Warning": QColor(220, 80, 30, 160),
    "Ice Storm Warning": QColor(150, 200, 255, 160),
}


@dataclass
class WarningPolygon:
    id: str
    issue_time: datetime
    expire_time: datetime
    type: str
    level: str
    severity_index: float
    confidence: float
    trigger_reason: List[str]
    affected_storm_id: int
    polygon: List[Tuple[float, float]]
    color: QColor = field(default_factory=lambda: QColor(255, 255, 255, 120))


class WarningEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.default_duration = config.get("default_duration_minutes", 45)
        self.pds_threshold = config.get("pds_severity_threshold", 0.75)
        self.emergency_threshold = config.get("emergency_threshold", 0.9)
        self._issued_cache: Dict[str, WarningPolygon] = {}

    def generate(
        self,
        detections: Sequence[Detection],
        storms: Iterable[StormCell],
        products: Dict[str, np.ndarray],
        sim_start: datetime,
        minute_offset: int,
        lon_grid: np.ndarray,
        lat_grid: np.ndarray,
    ) -> List[WarningPolygon]:
        timestamp = sim_start + timedelta(minutes=minute_offset)
        warnings: List[WarningPolygon] = []
        # Convert detections to warnings
        for detection in detections:
            if detection.name == "tornado":
                warnings.append(self._build_tornado_warning(detection, timestamp))
            elif detection.name == "hail":
                warnings.append(self._build_hail_warning(detection, timestamp))
            elif detection.name == "bow_echo":
                warnings.append(self._build_svr_warning(detection, timestamp))
            elif detection.name == "flash_flood":
                warnings.append(self._build_flood_warning(detection, timestamp))
            elif detection.name == "damaging_wind":
                warnings.append(self._build_wind_warning(detection, timestamp))

        # Additional winter or fire weather logic based on reflectivity fields.
        refl = products["Reflectivity"]
        snow_mask = refl < 35
        if snow_mask.sum() > 10000:
            centroid = self._centroid(snow_mask, lon_grid, lat_grid)
            warnings.append(self._simple_warning(
                warning_type="Winter Storm Warning",
                level="Normal",
                severity=0.5,
                confidence=0.6,
                centroid=centroid,
                reasons=["Widespread stratiform precipitation"],
                timestamp=timestamp,
            ))

        dry_mask = refl < 5
        if dry_mask.mean() > 0.6:
            centroid = self._centroid(dry_mask, lon_grid, lat_grid)
            warnings.append(self._simple_warning(
                warning_type="Red Flag Warning",
                level="Normal",
                severity=0.4,
                confidence=0.5,
                centroid=centroid,
                reasons=["Large dry sector – go easy on the campfires"],
                timestamp=timestamp,
            ))

        return warnings

    # ------------------------------------------------------------------
    def _build_tornado_warning(self, detection: Detection, timestamp: datetime) -> WarningPolygon:
        level = "Normal"
        if detection.score >= self.emergency_threshold:
            warning_type = "Tornado Emergency"
            level = "Emergency"
        elif detection.score >= self.pds_threshold:
            warning_type = "PDS Tornado Warning"
            level = "PDS"
        else:
            warning_type = "Tornado Warning"
        return self._polygon_from_detection(detection, warning_type, level, timestamp)

    def _build_hail_warning(self, detection: Detection, timestamp: datetime) -> WarningPolygon:
        level = "PDS" if detection.score > 0.85 else "Normal"
        warning_type = "Severe Hail Warning"
        return self._polygon_from_detection(detection, warning_type, level, timestamp)

    def _build_svr_warning(self, detection: Detection, timestamp: datetime) -> WarningPolygon:
        level = "PDS" if detection.score > 0.8 else "Normal"
        warning_type = "Severe Thunderstorm Warning"
        if level == "PDS":
            warning_type = "PDS Severe Thunderstorm Warning"
        return self._polygon_from_detection(detection, warning_type, level, timestamp)

    def _build_flood_warning(self, detection: Detection, timestamp: datetime) -> WarningPolygon:
        level = "PDS" if detection.score > 0.75 else "Normal"
        warning_type = "Flash Flood Warning"
        if level == "PDS":
            warning_type = "PDS Flash Flood Warning"
        return self._polygon_from_detection(detection, warning_type, level, timestamp)

    def _build_wind_warning(self, detection: Detection, timestamp: datetime) -> WarningPolygon:
        level = "Normal"
        if detection.score > 0.9:
            level = "PDS"
        warning_type = "Damaging Wind Warning"
        return self._polygon_from_detection(detection, warning_type, level, timestamp)

    def _simple_warning(
        self,
        warning_type: str,
        level: str,
        severity: float,
        confidence: float,
        centroid: Tuple[float, float],
        reasons: List[str],
        timestamp: datetime,
    ) -> WarningPolygon:
        issue = timestamp
        expire = issue + timedelta(minutes=self.default_duration)
        lon, lat = centroid
        polygon = self._square_polygon(lon, lat, 2.5)
        return WarningPolygon(
            id=f"{warning_type}-{issue.timestamp():.0f}",
            issue_time=issue,
            expire_time=expire,
            type=warning_type,
            level=level,
            severity_index=severity,
            confidence=confidence,
            trigger_reason=reasons,
            affected_storm_id=-1,
            polygon=polygon,
            color=WARNING_COLORS.get(warning_type, QColor(255, 255, 255, 140)),
        )

    def _polygon_from_detection(
        self,
        detection: Detection,
        warning_type: str,
        level: str,
        timestamp: datetime,
    ) -> WarningPolygon:
        issue = timestamp
        expire = issue + timedelta(minutes=self.default_duration)
        lon, lat = detection.centroid
        size = 2.0 + detection.score * 4.0
        polygon = self._square_polygon(lon, lat, size)
        warning_id = f"{warning_type}-{detection.affected_storm_id}-{issue.timestamp():.0f}"
        return WarningPolygon(
            id=warning_id,
            issue_time=issue,
            expire_time=expire,
            type=warning_type,
            level=level,
            severity_index=detection.score,
            confidence=min(1.0, detection.score + 0.2),
            trigger_reason=detection.reasons,
            affected_storm_id=detection.affected_storm_id,
            polygon=polygon,
            color=WARNING_COLORS.get(warning_type, QColor(255, 255, 255, 140)),
        )

    # ------------------------------------------------------------------
    def _square_polygon(self, lon: float, lat: float, half_width_deg: float) -> List[Tuple[float, float]]:
        return [
            (lon - half_width_deg, lat - half_width_deg),
            (lon + half_width_deg, lat - half_width_deg),
            (lon + half_width_deg, lat + half_width_deg),
            (lon - half_width_deg, lat + half_width_deg),
        ]

    def _centroid(self, mask: np.ndarray, lon_grid: np.ndarray, lat_grid: np.ndarray) -> Tuple[float, float]:
        indices = np.argwhere(mask)
        if len(indices) == 0:
            return float(lon_grid[len(lon_grid) // 2]), float(lat_grid[len(lat_grid) // 2])
        y_mean, x_mean = indices.mean(axis=0)
        lon = float(np.interp(x_mean, np.arange(len(lon_grid)), lon_grid))
        lat = float(np.interp(y_mean, np.arange(len(lat_grid)), lat_grid))
        return lon, lat


__all__ = ["WarningPolygon", "WarningEngine", "warn", "simplefilter", "filterwarnings"]
