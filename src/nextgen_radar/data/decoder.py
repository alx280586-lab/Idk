"""Decode radar frames into structured arrays."""

from __future__ import annotations

import datetime as dt
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import xarray as xr

from .sources import RadarFrame

try:  # pragma: no cover - optional dependency
    from metpy.io import Level2File
except Exception:  # pragma: no cover
    Level2File = None


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
        if Level2File is None:
            raise RuntimeError(
                "metpy is required to decode Level II volumes automatically. Install the optional dependency."
            )
        source_path: Optional[Path]
        temp_path: Optional[Path] = None
        if frame.path is not None:
            source_path = frame.path
        else:
            if frame.data is None:
                raise ValueError("LEVEL2 frame requires a file path or binary payload")
            temp_fd, temp_name = tempfile.mkstemp(suffix=".ar2v")
            os.close(temp_fd)
            temp_path = Path(temp_name)
            temp_path.write_bytes(frame.data)
            source_path = temp_path
        volumes: List[RadarVolume] = []
        try:
            with source_path.open("rb") as handle:
                level2 = Level2File(handle)
            station = getattr(level2, "station", None) or frame.station
            sweep_count = len(getattr(level2, "sweeps", []))
            base_time = frame.timestamp if frame.timestamp.tzinfo else frame.timestamp.replace(tzinfo=dt.timezone.utc)
            for sweep_index in range(sweep_count):
                azimuth, ranges_km, elevation = self._level2_geometry(level2, sweep_index, frame.elevation)
                sweep_time = self._level2_timestamp(level2, sweep_index, base_time)
                raw_moments = self._extract_moments(level2, sweep_index)
                sweep_volumes = self._build_volumes_for_sweep(
                    raw_moments,
                    azimuth,
                    ranges_km,
                    station,
                    elevation,
                    sweep_time,
                    sweep_index,
                )
                volumes.extend(sweep_volumes)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        return volumes

    def _extract_moments(
        self, level2: "Level2File", sweep_index: int
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        moment_aliases: Dict[str, Sequence[str]] = {
            "REF": ("REF", "DZ", "DBZ"),
            "VEL": ("VEL", "DV", "VR"),
            "SW": ("SW", "SR"),
            "ZDR": ("ZDR", "ZD"),
            "RHO": ("RHO", "RHOHV", "CC"),
            "KDP": ("KDP",),
            "PHI": ("PHI", "PHIDP"),
        }
        extracted: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        for key, aliases in moment_aliases.items():
            payload = self._get_level2_field(level2, sweep_index, aliases)
            if payload is None:
                continue
            data, azimuth, ranges = payload
            extracted[key] = (data, azimuth, ranges)
        if "KDP" not in extracted and "PHI" in extracted:
            phi_data, azimuth, ranges = extracted["PHI"]
            kdp = self._estimate_kdp(phi_data, ranges)
            extracted["KDP"] = (kdp, azimuth, ranges)
        return extracted

    def _build_volumes_for_sweep(
        self,
        raw_moments: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]],
        azimuth: np.ndarray,
        ranges_km: np.ndarray,
        station: str,
        elevation: float,
        sweep_time: dt.datetime,
        sweep_index: int,
    ) -> List[RadarVolume]:
        units_map = {
            "REF": "dBZ",
            "VEL": "m/s",
            "SW": "m/s",
            "ZDR": "dB",
            "RHO": "ratio",
            "KDP": "deg/km",
        }
        product_map = {
            "REF": "REF",
            "VEL": "VEL",
            "SW": "SW",
            "ZDR": "ZDR",
            "RHO": "CC",
            "KDP": "KDP",
        }
        volumes: List[RadarVolume] = []
        for key, (data, data_azimuth, data_range) in raw_moments.items():
            if key not in product_map:
                continue
            if data.size == 0:
                continue
            # Align geometry if the moment provides its own coordinates
            az = data_azimuth if data_azimuth.size else azimuth
            rng = data_range if data_range.size else ranges_km
            filled = np.ma.filled(np.asarray(data, dtype=np.float32), np.nan)
            moment = xr.DataArray(
                filled,
                dims=("azimuth", "range"),
                coords={"azimuth": az, "range": rng},
                attrs={"units": units_map.get(key, "")},
            )
            product_id = product_map[key]
            product_name = product_id if sweep_index == 0 else f"{product_id}_T{elevation:.2f}"
            volumes.append(
                RadarVolume(
                    product=product_name,
                    timestamp=sweep_time,
                    elevation=elevation,
                    station=station,
                    sweep=moment,
                    attributes={"tilt_degrees": elevation},
                    tilt_index=sweep_index,
                )
            )
        return volumes

    def _get_level2_field(
        self, level2: "Level2File", sweep_index: int, aliases: Sequence[str]
    ) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        for alias in aliases:
            try:
                payload = level2.get_data(sweep_index, alias)
            except KeyError:
                continue
            except Exception:
                continue
            if payload is None:
                continue
            data: Optional[np.ndarray]
            azimuth: Optional[np.ndarray]
            ranges: Optional[np.ndarray]
            if isinstance(payload, tuple) and len(payload) >= 3:
                data, azimuth, ranges = payload[0], payload[1], payload[2]
            elif isinstance(payload, dict):
                data = payload.get("data")
                azimuth = payload.get("azimuth") or payload.get("az")
                ranges = payload.get("range") or payload.get("r")
            else:
                continue
            if data is None or azimuth is None or ranges is None:
                continue
            return (np.asarray(data), np.asarray(azimuth), np.asarray(ranges))
        return None

    def _level2_geometry(
        self, level2: "Level2File", sweep_index: int, fallback_elevation: float
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        sweep = level2.sweeps[sweep_index]
        azimuths: List[float] = []
        elevations: List[float] = []
        for ray in sweep:
            header = getattr(ray, "header", None)
            if header is None and isinstance(ray, tuple):
                header = ray[0]
            elevation = None
            azimuth = None
            if header is not None:
                elevation = getattr(header, "elevation", None)
                if elevation is None:
                    elevation = getattr(header, "elev_angle", None)
                azimuth = getattr(header, "azimuth", None)
                if azimuth is None:
                    azimuth = getattr(header, "az_angle", None)
            if elevation is not None:
                elevations.append(float(elevation))
            if azimuth is not None:
                azimuths.append(float(azimuth))
        if not azimuths:
            data = self._get_level2_field(level2, sweep_index, ("REF",))
            if data is not None:
                azimuths = data[1].tolist()
        if not azimuths:
            azimuths = np.linspace(0, 360, 360, endpoint=False).tolist()
        elevation = float(np.nanmedian(elevations)) if elevations else float(fallback_elevation)
        ranges = self._get_level2_field(level2, sweep_index, ("REF",))
        if ranges is not None and ranges[2].size:
            range_values = ranges[2]
        else:
            gate_count = 460
            gate_spacing_km = 0.25
            range_values = np.linspace(0, (gate_count - 1) * gate_spacing_km, gate_count)
        range_values = np.asarray(range_values, dtype=np.float32)
        if range_values.max() > 1000:  # convert to km if necessary
            range_values = range_values / 1000.0
        return np.asarray(azimuths, dtype=np.float32), range_values, elevation

    def _level2_timestamp(
        self, level2: "Level2File", sweep_index: int, default: dt.datetime
    ) -> dt.datetime:
        sweep = level2.sweeps[sweep_index]
        times: List[dt.datetime] = []
        for ray in sweep:
            header = getattr(ray, "header", None)
            if header is None and isinstance(ray, tuple):
                header = ray[0]
            ray_time = None
            if header is not None:
                ray_time = getattr(header, "datetime", None)
                if ray_time is None:
                    seconds = getattr(header, "time", None)
                    days = getattr(header, "date", None)
                    if seconds is not None and days is not None:
                        try:
                            ref = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
                            ray_time = ref + dt.timedelta(days=int(days), seconds=float(seconds))
                        except Exception:
                            ray_time = None
            if isinstance(ray_time, dt.datetime):
                if ray_time.tzinfo is None:
                    ray_time = ray_time.replace(tzinfo=dt.timezone.utc)
                times.append(ray_time)
        if times:
            return max(times)
        return default

    def _estimate_kdp(self, phi: np.ndarray, ranges: np.ndarray) -> np.ndarray:
        phi_array = np.ma.filled(np.asarray(phi, dtype=np.float32), np.nan)
        if phi_array.ndim != 2 or phi_array.shape[1] < 2:
            return phi_array
        dr = np.diff(ranges)
        if dr.size == 0:
            return phi_array
        gradient = np.empty_like(phi_array, dtype=np.float32)
        gradient[:, 0] = np.nan
        gradient[:, 1:] = (phi_array[:, 1:] - phi_array[:, :-1]) / dr[np.newaxis, :]
        return gradient * 0.5


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

