"""Storm analysis algorithms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

import numpy as np
import xarray as xr


@dataclass(slots=True)
class StormWarning:
    """Represents an active storm warning polygon."""

    warning_type: str
    severity: str
    expires: str
    polygon: Sequence[Sequence[float]]


@dataclass(slots=True)
class StormFeature:
    feature_type: str
    azimuth: float
    range_km: float
    confidence: float


@dataclass(slots=True)
class StormSummary:
    warnings: List[StormWarning]
    features: List[StormFeature]


def detect_mesocyclone(velocity: xr.DataArray, shear_threshold: float = 20.0) -> List[StormFeature]:
    gradients = np.gradient(velocity.values)
    shear = gradients[1] - gradients[0]
    mask = shear > shear_threshold
    features: List[StormFeature] = []
    indices = np.argwhere(mask)
    for az_idx, rng_idx in indices:
        features.append(
            StormFeature(
                feature_type="mesocyclone",
                azimuth=float(velocity.azimuth[az_idx]),
                range_km=float(velocity.range[rng_idx]),
                confidence=float(np.clip(shear[az_idx, rng_idx] / (shear_threshold * 2), 0, 1)),
            )
        )
    return features


def detect_hook_echo(reflectivity: xr.DataArray, curvature_threshold: float = 0.25) -> List[StormFeature]:
    refl = reflectivity.values
    gradient_y, gradient_x = np.gradient(refl)
    curl = gradient_x - gradient_y
    mask = curl > curvature_threshold
    indices = np.argwhere(mask)
    features = [
        StormFeature(
            feature_type="hook_echo",
            azimuth=float(reflectivity.azimuth[i]),
            range_km=float(reflectivity.range[j]),
            confidence=float(np.clip(curl[i, j], 0, 1)),
        )
        for i, j in indices
    ]
    return features


def estimate_hail(reflectivity: xr.DataArray, kdp: xr.DataArray) -> List[StormFeature]:
    probability = np.clip((reflectivity.values - 50) / 20 + kdp.values / 5, 0, 1)
    mask = probability > 0.5
    indices = np.argwhere(mask)
    features = [
        StormFeature(
            feature_type="hail_core",
            azimuth=float(reflectivity.azimuth[i]),
            range_km=float(reflectivity.range[j]),
            confidence=float(probability[i, j]),
        )
        for i, j in indices
    ]
    return features


def summarize_storms(
    volumes: Dict[str, xr.DataArray],
    warnings: Sequence[StormWarning],
) -> StormSummary:
    features: List[StormFeature] = []
    if "VEL" in volumes:
        features.extend(detect_mesocyclone(volumes["VEL"]))
    if "REF" in volumes:
        features.extend(detect_hook_echo(volumes["REF"]))
    if {"REF", "KDP"}.issubset(volumes):
        features.extend(estimate_hail(volumes["REF"], volumes["KDP"]))
    return StormSummary(warnings=list(warnings), features=features)
