"""Radar product definitions and derived field computations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List

import numpy as np
import xarray as xr


@dataclass(slots=True)
class RadarProduct:
    """Metadata for a radar product along with a compute function."""

    product_id: str
    display_name: str
    units: str
    compute: Callable[[xr.DataArray], xr.DataArray]
    colormap: str


def identity(data: xr.DataArray) -> xr.DataArray:
    return data


def storm_relative_motion(velocity: xr.DataArray, storm_motion: float = 30.0) -> xr.DataArray:
    """Compute storm-relative velocity."""

    result = velocity - storm_motion
    result.attrs["units"] = velocity.attrs.get("units", "m/s")
    result.name = "SRM"
    return result


def composite_reflectivity(sweeps: Iterable[xr.DataArray]) -> xr.DataArray:
    stacked = xr.concat(list(sweeps), dim="elevation")
    comp = stacked.max(dim="elevation")
    comp.attrs["units"] = "dBZ"
    comp.name = "Composite Reflectivity"
    return comp


def vertically_integrated_liquid(reflectivity: xr.DataArray, gate_height: float = 0.25) -> xr.DataArray:
    """Estimate VIL using a simplified methodology."""

    z_linear = 10 ** (reflectivity / 10)
    vil = (z_linear.sum(dim="range") * gate_height) / 3.44e8
    vil.attrs["units"] = "kg/m^2"
    vil.name = "VIL"
    return vil


def hail_probability(reflectivity: xr.DataArray, kdp: xr.DataArray) -> xr.DataArray:
    """Estimate hail probability based on reflectivity and KDP."""

    scaled_ref = np.clip((reflectivity - 45) / 30, 0, 1)
    scaled_kdp = np.clip(kdp / 3, 0, 1)
    probability = xr.apply_ufunc(lambda r, k: 100 * r * 0.6 + 100 * k * 0.4, scaled_ref, scaled_kdp)
    hail = probability.clip(min=0, max=100)
    hail.attrs["units"] = "%"
    hail.name = "Hail Probability"
    return hail


def build_default_products() -> Dict[str, RadarProduct]:
    return {
        "REF": RadarProduct("REF", "Reflectivity", "dBZ", identity, "reflectivity"),
        "VEL": RadarProduct("VEL", "Velocity", "m/s", identity, "velocity"),
        "CC": RadarProduct("CC", "Correlation Coefficient", "ratio", identity, "correlation"),
        "SW": RadarProduct("SW", "Spectrum Width", "m/s", identity, "spectrum"),
        "ZDR": RadarProduct("ZDR", "Differential Reflectivity", "dB", identity, "zdr"),
        "KDP": RadarProduct("KDP", "Specific Differential Phase", "deg/km", identity, "kdp"),
        "SRM": RadarProduct("SRM", "Storm Relative Motion", "m/s", identity, "velocity"),
        "CREF": RadarProduct("CREF", "Composite Reflectivity", "dBZ", identity, "reflectivity"),
        "VIL": RadarProduct("VIL", "Vertically Integrated Liquid", "kg/m^2", identity, "vil"),
        "HAIL": RadarProduct("HAIL", "Hail Probability", "%", identity, "hail"),
    }


def derived_products(volumes: Dict[str, xr.DataArray]) -> Dict[str, xr.DataArray]:
    outputs: Dict[str, xr.DataArray] = {}
    if "VEL" in volumes:
        outputs["SRM"] = storm_relative_motion(volumes["VEL"])
    if "REF" in volumes:
        outputs["VIL"] = vertically_integrated_liquid(volumes["REF"])
    if {"REF", "KDP"}.issubset(volumes):
        outputs["HAIL"] = hail_probability(volumes["REF"], volumes["KDP"])
    if any(key.startswith("REF_") for key in volumes):
        sweeps: List[xr.DataArray] = [data for key, data in volumes.items() if key.startswith("REF_")]
        outputs["CREF"] = composite_reflectivity(sweeps)
    return outputs
