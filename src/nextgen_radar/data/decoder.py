"""Decode radar frames into structured arrays."""

from __future__ import annotations

import datetime as dt
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import xarray as xr

from .sources import RadarFrame

try:  # pragma: no cover - optional dependency
    import pyart
except Exception:  # pragma: no cover
    pyart = None


@dataclass(slots=True)
class RadarVolume:
    """Structured representation of a radar volume."""

    product: str
    timestamp: dt.datetime
    elevation: float
    station: str
    sweep: xr.DataArray
    attributes: Dict[str, float]
    tilt_index: int = 0

    def to_json(self) -> Dict[str, object]:
        """Serialize the volume to a JSON-serializable structure."""
        return {
            "product": self.product,
            "timestamp": self.timestamp.isoformat(),
            "elevation": self.elevation,
            "station": self.station,
            "attributes": self.attributes,
            "tilt_index": self.tilt_index,
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
            "LEVEL2": self._decode_level2,
        }

    def register(self, product: str, decoder: callable) -> None:
        self._decoders[product.upper()] = decoder

    def decode(self, frame: RadarFrame) -> List[RadarVolume]:
        product = frame.product.upper()
        if frame.path and frame.path.suffix == ".nc":
            sweep = self._decode_netcdf(frame, product)
            return [
                RadarVolume(
                    product=product,
                    timestamp=frame.timestamp,
                    elevation=frame.elevation,
                    station=frame.station,
                    sweep=sweep,
                    attributes=frame.attributes,
                )
            ]
        decoder = self._decoders.get(product, self._decode_generic)
        if frame.data is None and product != "LEVEL2":
            raise ValueError("Radar frame is missing binary payload for decoding")
        result = decoder(frame)
        if isinstance(result, list):
            return result
        return [
            RadarVolume(
                product=product,
                timestamp=frame.timestamp,
                elevation=frame.elevation,
                station=frame.station,
                sweep=result,
                attributes=frame.attributes,
            )
        ]

    def _decode_reflectivity(self, frame: RadarFrame) -> xr.DataArray:
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

    def _decode_level2(self, frame: RadarFrame) -> List[RadarVolume]:
        if pyart is None:
            raise RuntimeError(
                "arm_pyart is required to decode Level II volumes automatically. Install the optional dependency."
            )
        source = frame.path if frame.path else frame.data
        if source is None:
            raise ValueError("LEVEL2 frame requires a file path or binary payload")
        radar = pyart.io.read_nexrad_archive(source)
        station = radar.metadata.get("instrument_name", frame.station)
        range_gates = radar.range["data"] / 1000.0
        sweep_starts = radar.sweep_start_ray_index["data"]
        sweep_ends = radar.sweep_end_ray_index["data"]
        fixed_angles = radar.fixed_angle["data"]
        base_time = frame.timestamp
        if base_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=dt.timezone.utc)
        if pyart is not None:
            util_module = getattr(pyart, "util", None)
            common_module = getattr(pyart, "common", None)
            if util_module is not None:
                try:
                    base_time = util_module.datetime_from_radar(radar)  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover
                    pass
            if common_module is not None:
                try:
                    base_time = common_module.datetime_from_radar(radar)  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover
                    pass

        field_map: Dict[str, List[str]] = {
            "REF": ["reflectivity", "dz"],
            "VEL": ["velocity", "vr"],
            "ZDR": ["differential_reflectivity", "zdr"],
            "CC": ["cross_correlation_ratio", "cc"],
            "SW": ["spectrum_width", "sw"],
            "KDP": ["specific_differential_phase", "kdp"],
        }

        volumes: List[RadarVolume] = []
        for tilt_index, (start, end) in enumerate(zip(sweep_starts, sweep_ends)):
            ray_slice = slice(int(start), int(end) + 1)
            azimuth = radar.azimuth["data"][ray_slice]
            sweep_seconds = float(np.nanmedian(radar.time["data"][ray_slice])) if radar.time["data"].size else 0.0
            sweep_time = base_time + dt.timedelta(seconds=sweep_seconds)
            for field_id, candidates in field_map.items():
                field_name = next((name for name in candidates if name in radar.fields), None)
                if not field_name:
                    continue
                data = radar.fields[field_name]["data"][ray_slice]
                array = xr.DataArray(
                    np.ma.filled(data, np.nan),
                    dims=("azimuth", "range"),
                    coords={"azimuth": azimuth, "range": range_gates},
                    attrs={
                        "units": radar.fields[field_name].get("units", ""),
                        "tilt": float(fixed_angles[tilt_index]),
                        "station": station,
                    },
                )
                product_name = field_id if tilt_index == 0 else f"{field_id}_T{fixed_angles[tilt_index]:.2f}"
                volumes.append(
                    RadarVolume(
                        product=product_name,
                        timestamp=sweep_time,
                        elevation=float(fixed_angles[tilt_index]),
                        station=station,
                        sweep=array,
                        attributes={"tilt_degrees": float(fixed_angles[tilt_index])},
                        tilt_index=tilt_index,
                    )
                )
        return volumes


def merge_volumes(volumes: Iterable[RadarVolume], product: str) -> Optional[RadarVolume]:
    """Merge multiple sweeps of the same product into a composite."""

    volumes = [vol for vol in volumes if vol.product == product]
    if not volumes:
        return None
    data = np.stack([vol.sweep.values for vol in volumes], axis=0)
    composite = np.nanmax(data, axis=0)
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
        elevation=first.elevation,
        station=first.station,
        sweep=sweep,
        attributes=first.attributes,
    )


__all__ = ["RadarDecoder", "RadarVolume", "merge_volumes"]

