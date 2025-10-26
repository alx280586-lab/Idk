"""Decode radar frames into structured arrays."""

from __future__ import annotations

import datetime as dt
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import numpy as np
import xarray as xr

from .sources import RadarFrame


@dataclass(slots=True)
class RadarVolume:
    """Structured representation of a radar volume."""

    product: str
    timestamp: dt.datetime
    elevation: float
    station: str
    sweep: xr.DataArray
    attributes: Dict[str, float]

    def to_json(self) -> Dict[str, object]:
        """Serialize the volume to a JSON-serializable structure."""
        return {
            "product": self.product,
            "timestamp": self.timestamp.isoformat(),
            "elevation": self.elevation,
            "station": self.station,
            "attributes": self.attributes,
            "shape": list(self.sweep.shape),
            "dtype": str(self.sweep.dtype),
        }


class RadarDecoder:
    """Decode raw radar frames using plugin decoders."""

    def __init__(self) -> None:
        self._decoders: Dict[str, callable] = {
            "REF": self._decode_reflectivity,
            "VEL": self._decode_velocity,
            "CC": self._decode_generic,
            "SW": self._decode_generic,
            "ZDR": self._decode_generic,
            "KDP": self._decode_generic,
        }

    def register(self, product: str, decoder: callable) -> None:
        self._decoders[product.upper()] = decoder

    def decode(self, frame: RadarFrame) -> RadarVolume:
        product = frame.product.upper()
        if frame.path and frame.path.suffix == ".nc":
            sweep = self._decode_netcdf(frame, product)
        else:
            decoder = self._decoders.get(product, self._decode_generic)
            if frame.data is None:
                raise ValueError("Radar frame is missing binary payload for decoding")
            sweep = decoder(frame)
        return RadarVolume(
            product=product,
            timestamp=frame.timestamp,
            elevation=frame.elevation,
            station=frame.station,
            sweep=sweep,
            attributes=frame.attributes,
        )

    def _decode_reflectivity(self, frame: RadarFrame) -> xr.DataArray:
        if frame.data is None:
            raise ValueError("Reflectivity frame requires binary payload")
        data = np.frombuffer(frame.data, dtype=np.int16)
        grid = data.reshape((360, -1)) / 2.0 - 32.0
        azimuth = np.linspace(0, 360, grid.shape[0], endpoint=False)
        range_gate = np.arange(grid.shape[1]) * 0.25
        return xr.DataArray(
            grid,
            dims=("azimuth", "range"),
            coords={"azimuth": azimuth, "range": range_gate},
            attrs={"units": "dBZ"},
        )

    def _decode_velocity(self, frame: RadarFrame) -> xr.DataArray:
        if frame.data is None:
            raise ValueError("Velocity frame requires binary payload")
        data = np.frombuffer(frame.data, dtype=np.int16)
        grid = data.reshape((360, -1)) / 256.0 * 60.0
        azimuth = np.linspace(0, 360, grid.shape[0], endpoint=False)
        range_gate = np.arange(grid.shape[1]) * 0.25
        return xr.DataArray(
            grid,
            dims=("azimuth", "range"),
            coords={"azimuth": azimuth, "range": range_gate},
            attrs={"units": "m/s"},
        )

    def _decode_generic(self, frame: RadarFrame) -> xr.DataArray:
        if frame.data is None:
            raise ValueError("Generic frame requires binary payload")
        data = np.frombuffer(frame.data, dtype=np.float32)
        try:
            grid = data.reshape((360, -1))
        except ValueError:
            grid = np.interp(
                np.linspace(0, data.size - 1, 360 * 460),
                np.arange(data.size),
                data,
            ).reshape((360, 460))
        azimuth = np.linspace(0, 360, grid.shape[0], endpoint=False)
        range_gate = np.arange(grid.shape[1]) * 0.25
        return xr.DataArray(
            grid,
            dims=("azimuth", "range"),
            coords={"azimuth": azimuth, "range": range_gate},
        )

    def _decode_netcdf(self, frame: RadarFrame, product: str) -> xr.DataArray:
        dataset = self._open_dataset(frame)
        try:
            data_var = self._select_data_variable(dataset, product)
            sweep = data_var.squeeze()
            if "time" in sweep.dims:
                sweep = sweep.isel(time=-1, drop=True)
            rename = {}
            for dim in sweep.dims:
                lower = dim.lower()
                if lower.startswith("az") and dim != "azimuth":
                    rename[dim] = "azimuth"
                elif lower.startswith("ra") and dim != "range":
                    rename[dim] = "range"
            if rename:
                sweep = sweep.rename(rename)
            return sweep
        finally:
            temp_path = dataset.attrs.pop("_temp_path", None)
            dataset.close()
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    def _open_dataset(self, frame: RadarFrame) -> xr.Dataset:
        if frame.path and frame.path.exists():
            dataset = xr.open_dataset(frame.path)
            return dataset
        if frame.data is None:
            raise ValueError("Radar frame does not contain NetCDF data")
        temp_fd, temp_name = tempfile.mkstemp(suffix=".nc")
        os.close(temp_fd)
        temp_path = Path(temp_name)
        temp_path.write_bytes(frame.data)
        dataset = xr.open_dataset(temp_path)
        dataset.attrs["_temp_path"] = str(temp_path)
        return dataset

    def _select_data_variable(self, dataset: xr.Dataset, product: str) -> xr.DataArray:
        preferences = {
            "REF": ["Reflectivity", "Reflectivity_HI", "REF", "DZ"],
            "VEL": ["Velocity", "RadialVelocity", "VEL", "VR"],
            "CC": ["CorrelationCoefficient", "CC"],
            "SW": ["SpectrumWidth", "SW"],
            "ZDR": ["DifferentialReflectivity", "ZDR"],
            "KDP": ["SpecificDifferentialPhase", "KDP"],
        }
        candidates = [product] + preferences.get(product, [])
        for candidate in candidates:
            if candidate in dataset.data_vars:
                return dataset[candidate]
            lower = candidate.lower()
            for name in dataset.data_vars:
                if name.lower() == lower:
                    return dataset[name]
        if dataset.data_vars:
            return next(iter(dataset.data_vars.values()))
        raise ValueError(f"No data variables found in NetCDF dataset for product {product}")


def merge_volumes(volumes: Iterable[RadarVolume], product: str) -> Optional[RadarVolume]:
    """Merge multiple sweeps of the same product into a composite."""

    volumes = [vol for vol in volumes if vol.product == product]
    if not volumes:
        return None
    data = np.stack([vol.sweep.values for vol in volumes], axis=0)
    composite = data.max(axis=0)
    first = volumes[0]
    sweep = xr.DataArray(
        composite,
        dims=first.sweep.dims,
        coords=first.sweep.coords,
        attrs={"units": first.sweep.attrs.get("units", "")},
    )
    return RadarVolume(
        product=f"{product}_COMPOSITE",
        timestamp=max(vol.timestamp for vol in volumes),
        elevation=float(np.mean([vol.elevation for vol in volumes])),
        station=first.station,
        sweep=sweep,
        attributes=first.attributes,
    )
