"""Feature detectors for the synthetic radar simulator.

These operate on the gridded radar data produced by :mod:`storm_generator` and
return qualitative signals that the warning engine can consume.  The logic is
purposely heuristic – we're not training a neural net here – but we sprinkle in
just enough meteorological reasoning to make the output feel educational.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List
import numpy as np


@dataclass
class Detection:
    name: str
    score: float
    centroid: tuple[float, float]
    affected_storm_id: int
    reasons: List[str]


class DetectorSuite:
    """Collection of detectors driven by configuration thresholds."""

    def __init__(self, config: Dict[str, float]):
        self.config = config

    def run_all(self, products: Dict[str, np.ndarray], storms: Iterable, lon_grid, lat_grid) -> List[Detection]:
        detections: List[Detection] = []
        detections.extend(self._detect_tornado(products, storms, lon_grid, lat_grid))
        detections.extend(self._detect_hail(products, storms, lon_grid, lat_grid))
        detections.extend(self._detect_bow(products, storms, lon_grid, lat_grid))
        detections.extend(self._detect_flash_flood(products, storms, lon_grid, lat_grid))
        detections.extend(self._detect_wind(products, storms, lon_grid, lat_grid))
        return detections

    # ------------------------------------------------------------------
    def _detect_tornado(self, products, storms, lon_grid, lat_grid) -> List[Detection]:
        refl = products["Reflectivity"]
        vel = products["Velocity"]
        cc = products["Correlation Coefficient"]
        sw = products["Spectrum Width"]
        detections: List[Detection] = []
        shear_thresh = self.config.get("tornado_shear_threshold", 35.0)
        refl_thresh = self.config.get("tornado_reflectivity_threshold", 45.0)
        debris_cc = self.config.get("debris_cc_threshold", 0.82)
        debris_sw = self.config.get("debris_spectrum_threshold", 5.0)

        grad_y, grad_x = np.gradient(vel)
        shear = np.hypot(grad_x, grad_y)
        shear_mask = shear > shear_thresh
        strong_reflectivity = refl > refl_thresh
        cc_drop = cc < debris_cc
        sw_high = sw > debris_sw

        for storm in storms:
            y_idx = np.searchsorted(lat_grid, storm.lat)
            x_idx = np.searchsorted(lon_grid, storm.lon)
            window = np.s_[max(0, y_idx - 6): y_idx + 6, max(0, x_idx - 6): x_idx + 6]
            shear_hits = shear_mask[window].sum()
            debris_hits = (cc_drop & sw_high & strong_reflectivity)[window].sum()
            if shear_hits > 10:
                score = min(1.0, 0.5 + shear_hits / 80.0)
                reasons = [f"Velocity shear gate count {shear_hits}"]
                if debris_hits > 3:
                    score += 0.2
                    reasons.append("Debris signature co-located with shear")
                detections.append(
                    Detection(
                        name="tornado",
                        score=score,
                        centroid=(storm.lon, storm.lat),
                        affected_storm_id=storm.storm_id,
                        reasons=reasons,
                    )
                )
        return detections

    def _detect_hail(self, products, storms, lon_grid, lat_grid) -> List[Detection]:
        refl = products["Reflectivity"]
        zdr = products["Differential Reflectivity"]
        cc = products["Correlation Coefficient"]
        hail_ref = self.config.get("hail_reflectivity_threshold", 58.0)
        zdr_drop = self.config.get("hail_zdr_drop", 0.5)
        detections: List[Detection] = []
        for storm in storms:
            y_idx = np.searchsorted(lat_grid, storm.lat)
            x_idx = np.searchsorted(lon_grid, storm.lon)
            window = np.s_[max(0, y_idx - 10): y_idx + 10, max(0, x_idx - 10): x_idx + 10]
            intense = refl[window] > hail_ref
            zdr_low = zdr[window] < 1.0 - zdr_drop
            cc_low = cc[window] < 0.9
            hail_score = 0.0
            if intense.sum() > 15:
                hail_score += 0.4
            if (intense & zdr_low).sum() > 8:
                hail_score += 0.3
            if (intense & cc_low).sum() > 5:
                hail_score += 0.2
            if hail_score > 0:
                detections.append(
                    Detection(
                        name="hail",
                        score=min(1.0, hail_score + storm.severity * 0.3),
                        centroid=(storm.lon, storm.lat),
                        affected_storm_id=storm.storm_id,
                        reasons=["Co-located high dBZ and low ZDR"],
                    )
                )
        return detections

    def _detect_bow(self, products, storms, lon_grid, lat_grid) -> List[Detection]:
        vel = products["Velocity"]
        bow_thresh = self.config.get("bow_velocity_threshold", 22.0)
        detections: List[Detection] = []
        for storm in storms:
            y_idx = np.searchsorted(lat_grid, storm.lat)
            x_idx = np.searchsorted(lon_grid, storm.lon)
            window = np.s_[max(0, y_idx - 16): y_idx + 16, max(0, x_idx - 16): x_idx + 16]
            outbound = vel[window] > bow_thresh
            inbound = vel[window] < -bow_thresh
            ratio = outbound.sum() / max(1, inbound.sum())
            if outbound.sum() > 40 and ratio > 1.5:
                detections.append(
                    Detection(
                        name="bow_echo",
                        score=min(1.0, 0.5 + outbound.mean() / 40.0),
                        centroid=(storm.lon, storm.lat),
                        affected_storm_id=storm.storm_id,
                        reasons=["Strong outbound momentum on leading edge"],
                    )
                )
        return detections

    def _detect_flash_flood(self, products, storms, lon_grid, lat_grid) -> List[Detection]:
        kdp = products["Specific Differential Phase"]
        refl = products["Reflectivity"]
        kdp_thresh = self.config.get("flooding_kdp_threshold", 2.0)
        detections: List[Detection] = []
        heavy = (kdp > kdp_thresh) & (refl > 45)
        if heavy.sum() > 300:
            centroid = self._centroid_from_mask(heavy, lon_grid, lat_grid)
            detections.append(
                Detection(
                    name="flash_flood",
                    score=min(1.0, heavy.mean()),
                    centroid=centroid,
                    affected_storm_id=-1,
                    reasons=["Persistent high KDP suggesting excessive rain"],
                )
            )
        return detections

    def _detect_wind(self, products, storms, lon_grid, lat_grid) -> List[Detection]:
        vel = products["Velocity"]
        threshold = self.config.get("wind_damage_threshold", 28.0)
        detections: List[Detection] = []
        strong = np.abs(vel) > threshold
        if strong.sum() > 200:
            centroid = self._centroid_from_mask(strong, lon_grid, lat_grid)
            detections.append(
                Detection(
                    name="damaging_wind",
                    score=min(1.0, np.abs(vel[strong]).mean() / 45.0),
                    centroid=centroid,
                    affected_storm_id=-1,
                    reasons=["Widespread high-velocity pixels"],
                )
            )
        return detections

    # ------------------------------------------------------------------
    def _centroid_from_mask(self, mask: np.ndarray, lon_grid, lat_grid) -> tuple[float, float]:
        indices = np.argwhere(mask)
        if len(indices) == 0:
            return float(lon_grid[len(lon_grid) // 2]), float(lat_grid[len(lat_grid) // 2])
        y_mean, x_mean = indices.mean(axis=0)
        lon = float(np.interp(x_mean, np.arange(len(lon_grid)), lon_grid))
        lat = float(np.interp(y_mean, np.arange(len(lat_grid)), lat_grid))
        return lon, lat


__all__ = ["DetectorSuite", "Detection"]
