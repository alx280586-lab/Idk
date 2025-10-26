"""Synthetic storm generator producing radar-like fields.

This module builds a cartoon version of radar meteorology.  The goal is not to
match any real radar, but to create believable structures that resemble radar
signatures described in operational training.  Every storm cell carries a full
set of dual-polarimetric variables and velocity information so the GUI can
switch between products without recomputing the physics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import math
import numpy as np
from scipy.ndimage import gaussian_filter


@dataclass
class StormCell:
    """State carried forward through the simulation.

    Attributes
    ----------
    storm_id: int
        Unique identifier for the storm.
    kind: str
        Storm type (e.g., ``"supercell"`` or ``"bow_echo"``).
    lon: float
        Longitude of the storm centroid.
    lat: float
        Latitude of the storm centroid.
    motion_u: float
        Eastward motion (m/s).
    motion_v: float
        Northward motion (m/s).
    peak_dbz: float
        Maximum reflectivity target for this storm.
    severity: float
        0-1 metric summarising intensity; used by the warning logic.
    age_minutes: int
        Minutes since the storm spawned.
    lifecycle_minutes: int
        Total expected lifetime.
    hook_direction: float
        Orientation for hook echoes (radians clockwise from north).
    notes: List[str]
        Debug/diagnostic comments about simulated phenomena.
    """

    storm_id: int
    kind: str
    lon: float
    lat: float
    motion_u: float
    motion_v: float
    peak_dbz: float
    severity: float
    age_minutes: int = 0
    lifecycle_minutes: int = 180
    hook_direction: float = 0.0
    notes: List[str] = field(default_factory=list)

    def advance(self, minutes: int) -> None:
        """Move the storm according to its motion and age it."""
        distance_east = self.motion_u * minutes
        distance_north = self.motion_v * minutes
        # Convert metres to degrees (very crude but fine for a cartoon).
        self.lon += (distance_east / 1000.0) / 111.0 / math.cos(math.radians(self.lat))
        self.lat += (distance_north / 1000.0) / 111.0
        self.age_minutes += minutes
        # Ramp severity up/down through life cycle.
        life_fraction = min(1.0, self.age_minutes / max(1, self.lifecycle_minutes))
        envelope = math.sin(math.pi * min(1.0, life_fraction))
        self.severity = max(0.05, self.severity * 0.7 + 0.3 * envelope)

    @property
    def alive(self) -> bool:
        return self.age_minutes < self.lifecycle_minutes


@dataclass
class RadarFrame:
    """Container for per-time-step radar grids."""

    timestamp_minutes: int
    products: Dict[str, np.ndarray]
    storms: List[StormCell]
    metadata: Dict[str, float]


class SyntheticStormModel:
    """High level API for the simulator.

    The model integrates a collection of storm cells on a fixed longitude/latitude
    grid covering the continental United States.  The simulation keeps track of a
    full suite of dual-pol radar moments for every frame so that the UI can scrub
    forward/backward instantly.
    """

    def __init__(self, config: Dict):
        self.config = config
        sim = config["simulation"]
        self.seed = sim.get("seed", 42)
        self.duration_hours = sim.get("duration_hours", 24)
        self.timestep_minutes = sim.get("timestep_minutes", 5)
        self.grid_width = sim.get("grid_width", 360)
        self.grid_height = sim.get("grid_height", 220)
        self.lon_min = sim.get("lon_min", -125.0)
        self.lon_max = sim.get("lon_max", -66.0)
        self.lat_min = sim.get("lat_min", 24.0)
        self.lat_max = sim.get("lat_max", 50.0)
        self.env_wind = sim.get("base_environmental_wind", 15.0)
        self.nyquist = sim.get("nyquist_velocity", 28.0)
        self.radar_origin = (sim.get("radar_origin_lon", -98.0), sim.get("radar_origin_lat", 36.0))
        self.clutter_ring_radius = sim.get("clutter_ring_radius_km", 40.0)
        self.noise_level = sim.get("noise_level", 1.0)
        self.composite_tilts = sim.get("composite_tilts", 4)
        render = config.get("rendering", {})
        self.blur_sigma = render.get("blur_sigma", 1.2)
        self.beam_broadening_rate = render.get("beam_broadening_rate", 0.001)

        self.lon_grid = np.linspace(self.lon_min, self.lon_max, self.grid_width)
        self.lat_grid = np.linspace(self.lat_min, self.lat_max, self.grid_height)
        self.lon2d, self.lat2d = np.meshgrid(self.lon_grid, self.lat_grid)
        self.cos_lat = np.cos(np.deg2rad(self.lat2d))
        self.earth_radius_km = 6371.0
        self.random = np.random.default_rng(self.seed)
        self._storm_id_counter = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_day(self) -> List[RadarFrame]:
        """Simulate the whole day returning a list of frames."""
        total_minutes = int(self.duration_hours * 60)
        frames: List[RadarFrame] = []
        active_storms: List[StormCell] = []
        storm_types = self.config.get("storm_types", {})
        spawn_bias = self._build_spawn_bias()

        for minute in range(0, total_minutes, self.timestep_minutes):
            # Update storms, remove dead ones.
            for storm in list(active_storms):
                storm.advance(self.timestep_minutes)
                if not storm.alive:
                    active_storms.remove(storm)

            # Merge storms if they get too close.
            self._merge_close_storms(active_storms)

            # Spawn new storms according to climatology.
            spawn_chance = self.random.random()
            for kind, info in storm_types.items():
                if spawn_chance < info.get("probability", 0.1):
                    if self._count_kind(active_storms, kind) < info.get("max_count", 5):
                        new_storm = self._spawn_storm(kind, spawn_bias)
                        active_storms.append(new_storm)
                        break

            # Create the radar fields for this timestep.
            products = self._render_products(active_storms)
            metadata = {
                "storm_count": len(active_storms),
                "playback_minute": minute,
            }
            snapshot = [self._copy_storm(storm) for storm in active_storms]
            frames.append(RadarFrame(minute, products, snapshot, metadata))

        return frames

    # ------------------------------------------------------------------
    # Storm lifecycle helpers
    # ------------------------------------------------------------------
    def _count_kind(self, storms: List[StormCell], kind: str) -> int:
        return sum(1 for s in storms if s.kind == kind)

    def _spawn_storm(self, kind: str, spawn_bias: Dict[str, Tuple[float, float]]) -> StormCell:
        base_centroid = spawn_bias.get(kind, spawn_bias["generic"])
        jitter_lon = self.random.normal(scale=3.0)
        jitter_lat = self.random.normal(scale=2.0)
        lon = np.clip(base_centroid[0] + jitter_lon, self.lon_min + 1, self.lon_max - 1)
        lat = np.clip(base_centroid[1] + jitter_lat, self.lat_min + 1, self.lat_max - 1)
        motion_u = self.random.normal(loc=self.env_wind, scale=6.0)
        motion_v = self.random.normal(loc=2.0, scale=4.0)
        peak_dbz = {
            "supercell": self.random.uniform(58, 72),
            "bow_echo": self.random.uniform(50, 65),
            "pulse": self.random.uniform(40, 58),
            "winter": self.random.uniform(30, 45),
        }.get(kind, self.random.uniform(35, 55))
        lifecycle = {
            "supercell": self.random.integers(150, 240),
            "bow_echo": self.random.integers(120, 210),
            "pulse": self.random.integers(45, 120),
            "winter": self.random.integers(180, 360),
        }.get(kind, self.random.integers(60, 180))
        hook_dir = self.random.uniform(0, 2 * math.pi)
        storm = StormCell(
            storm_id=self._storm_id_counter,
            kind=kind,
            lon=float(lon),
            lat=float(lat),
            motion_u=float(motion_u),
            motion_v=float(motion_v),
            peak_dbz=float(peak_dbz),
            severity=self.random.uniform(0.4, 0.7),
            lifecycle_minutes=int(lifecycle),
            hook_direction=hook_dir,
        )
        self._storm_id_counter += 1
        storm.notes.append(f"Spawned {kind} storm with peak {storm.peak_dbz:.1f} dBZ")
        return storm

    def _build_spawn_bias(self) -> Dict[str, Tuple[float, float]]:
        return {
            "supercell": (-99.0, 36.5),  # Central Plains – home of spinny doom.
            "bow_echo": (-91.0, 40.0),
            "pulse": (-84.0, 32.0),
            "winter": (-103.0, 44.5),
            "generic": (-96.0, 37.0),
        }

    def _merge_close_storms(self, storms: List[StormCell]) -> None:
        merge_distance_km = 60.0
        merged: List[StormCell] = []
        for storm in storms:
            if storm in merged:
                continue
            for other in storms:
                if storm is other or other in merged:
                    continue
                dist = self._distance_km(storm.lon, storm.lat, other.lon, other.lat)
                if dist < merge_distance_km:
                    storm.peak_dbz = max(storm.peak_dbz, other.peak_dbz) + 5
                    storm.severity = min(1.0, storm.severity + other.severity * 0.5)
                    storm.notes.append(f"Merged with storm {other.storm_id} at {dist:.1f} km")
                    merged.append(other)
        for storm in merged:
            storms.remove(storm)

    def _copy_storm(self, storm: StormCell) -> StormCell:
        return StormCell(
            storm_id=storm.storm_id,
            kind=storm.kind,
            lon=storm.lon,
            lat=storm.lat,
            motion_u=storm.motion_u,
            motion_v=storm.motion_v,
            peak_dbz=storm.peak_dbz,
            severity=storm.severity,
            age_minutes=storm.age_minutes,
            lifecycle_minutes=storm.lifecycle_minutes,
            hook_direction=storm.hook_direction,
            notes=list(storm.notes),
        )

    # ------------------------------------------------------------------
    # Field rendering
    # ------------------------------------------------------------------
    def _render_products(self, storms: List[StormCell]) -> Dict[str, np.ndarray]:
        shape = (self.grid_height, self.grid_width)
        refl = np.full(shape, -10.0, dtype=np.float32)
        vel = np.full(shape, -self.env_wind * 0.5, dtype=np.float32)
        cc = np.full(shape, 0.99, dtype=np.float32)
        zdr = np.full(shape, 0.5, dtype=np.float32)
        kdp = np.full(shape, 0.1, dtype=np.float32)
        sw = np.full(shape, 1.2, dtype=np.float32)
        composite = np.full(shape, -10.0, dtype=np.float32)

        # Add environmental gradient to velocity so there is a background flow.
        vel += (self.lon2d - self.lon_min) / (self.lon_max - self.lon_min) * 6.0

        for storm in storms:
            self._render_storm(storm, refl, vel, cc, zdr, kdp, sw, composite)

        # Add clutter ring optionally.
        self._apply_clutter(refl)

        # Composite reflectivity is just a fancy max of blurred copies.
        composite[:] = np.maximum(composite, refl)
        for tilt in range(1, self.composite_tilts):
            decay = 1.0 - 0.12 * tilt
            composite[:] = np.maximum(composite, gaussian_filter(refl * decay, sigma=1 + 0.5 * tilt))

        # Gaussian blur to emulate beam smearing.
        sigma = self.blur_sigma
        refl_smoothed = gaussian_filter(refl, sigma=sigma)
        vel_smoothed = gaussian_filter(vel, sigma=sigma)
        cc_smoothed = gaussian_filter(cc, sigma=sigma * 0.5)
        zdr_smoothed = gaussian_filter(zdr, sigma=sigma * 0.7)
        kdp_smoothed = gaussian_filter(kdp, sigma=sigma * 0.7)
        sw_smoothed = gaussian_filter(sw, sigma=sigma)

        # Inject random speckle noise and small-scale features.
        noise = self.random.normal(scale=self.noise_level, size=refl.shape)
        refl_final = refl_smoothed + noise
        vel_final = vel_smoothed + self.random.normal(scale=1.5, size=vel.shape)
        cc_final = np.clip(cc_smoothed - np.abs(noise) * 0.002, 0.4, 1.0)
        zdr_final = zdr_smoothed + self.random.normal(scale=0.1, size=zdr.shape)
        kdp_final = kdp_smoothed + self.random.normal(scale=0.05, size=kdp.shape)
        sw_final = sw_smoothed + np.abs(self.random.normal(scale=0.2, size=sw.shape))

        return {
            "Reflectivity": refl_final.astype(np.float32),
            "Velocity": vel_final.astype(np.float32),
            "Spectrum Width": sw_final.astype(np.float32),
            "Correlation Coefficient": cc_final.astype(np.float32),
            "Differential Reflectivity": zdr_final.astype(np.float32),
            "Specific Differential Phase": kdp_final.astype(np.float32),
            "Composite Reflectivity": composite.astype(np.float32),
        }

    def _render_storm(
        self,
        storm: StormCell,
        refl: np.ndarray,
        vel: np.ndarray,
        cc: np.ndarray,
        zdr: np.ndarray,
        kdp: np.ndarray,
        sw: np.ndarray,
        composite: np.ndarray,
    ) -> None:
        """Place a storm's contribution into the radar fields."""
        lon_center = storm.lon
        lat_center = storm.lat

        distance_km = self._distance_km(lon_center, lat_center, self.lon2d, self.lat2d)
        direction_rad = np.arctan2(self.lon2d - lon_center, self.lat2d - lat_center)
        angle_offset = direction_rad.copy()

        base_scale = {
            "supercell": (90, 55),
            "bow_echo": (150, 70),
            "pulse": (60, 40),
            "winter": (220, 120),
        }.get(storm.kind, (80, 50))
        # Beam broadening – larger distance -> larger smoothing radius.
        beam_sigma = 1.0 + distance_km * self.beam_broadening_rate

        x_scale_km, y_scale_km = base_scale
        elliptical = np.exp(-(((distance_km * np.cos(direction_rad)) ** 2) / (2 * y_scale_km ** 2)
                               + ((distance_km * np.sin(direction_rad)) ** 2) / (2 * x_scale_km ** 2)))
        storm_core = elliptical * storm.peak_dbz
        storm_core = gaussian_filter(storm_core, sigma=beam_sigma)

        # Hook echo for supercells: add a curved appendage of higher reflectivity.
        if storm.kind == "supercell":
            hook_angle = storm.hook_direction
            angle_offset = (direction_rad - hook_angle + math.pi) % (2 * math.pi) - math.pi
            hook_mask = np.exp(-(angle_offset ** 2) / 0.6) * np.exp(-(distance_km - 15) ** 2 / (2 * 45 ** 2))
            hook = hook_mask * (storm.peak_dbz + 8)
            storm_core += hook
            # Weak echo region – remove reflectivity right next to rotation.
            inner = np.exp(-(distance_km ** 2) / (2 * 18 ** 2))
            storm_core -= inner * 15
            storm.notes.append("Hook echo carved with weak echo region")

        # Bow echo: emphasise leading edge and add a rear inflow notch.
        if storm.kind == "bow_echo":
            arc = np.exp(-((distance_km - 40) ** 2) / (2 * 25 ** 2))
            leading_edge = np.clip(np.cos(direction_rad - math.pi / 2), 0, 1)
            storm_core += leading_edge * arc * 35
            rear_inflow = np.exp(-((distance_km - 65) ** 2) / (2 * 20 ** 2)) * np.clip(-leading_edge, 0, 1)
            storm_core -= np.abs(rear_inflow) * 30

        # Pulse storms: tiny but occasionally intense.
        if storm.kind == "pulse":
            pulsation = 1.0 + 0.3 * math.sin(math.radians(storm.age_minutes * 12))
            storm_core *= pulsation

        # Winter storms: broad low reflectivity with embedded banding.
        if storm.kind == "winter":
            banding = np.sin((self.lon2d - lon_center) * 0.4) * np.cos((self.lat2d - lat_center) * 0.6)
            storm_core += banding * 5

        # Attenuation behind high-dBZ cores.  We assume the radar is west of the storm.
        attenuation = np.exp(-np.maximum(0, distance_km - 30) / 60.0)
        storm_core *= attenuation

        refl[:] = np.maximum(refl, storm_core)
        composite[:] = np.maximum(composite, storm_core)

        # Velocity signature: combination of storm motion and rotation.
        rotation_speed = {
            "supercell": 38.0,
            "bow_echo": 25.0,
            "pulse": 12.0,
            "winter": 8.0,
        }.get(storm.kind, 15.0)
        rotational = rotation_speed * np.sin(angle_offset if storm.kind == "supercell" else direction_rad)
        vel_field = storm.motion_u * 0.8 + rotational
        vel[:] += vel_field * elliptical * 0.7

        # Add tornado vortex signature when severity is high.
        if storm.kind == "supercell" and storm.severity > 0.75:
            vortex_radius_km = 8.0
            vortex = np.exp(-(distance_km ** 2) / (2 * vortex_radius_km ** 2))
            vel[:] += vortex * rotation_speed * 1.8
            sw[:] += vortex * 4.0
            cc[:] -= vortex * 0.22  # Debris field lowers CC.
            zdr[:] -= vortex * 0.8
            kdp[:] += vortex * 1.5
            storm.notes.append("Injected TVS / debris signature")

        # Outflow boundaries appear as thin rings expanding away.
        gust_radius = 25 + 0.4 * storm.age_minutes
        boundary = np.exp(-((distance_km - gust_radius) ** 2) / (2 * 8 ** 2))
        refl[:] = np.maximum(refl, boundary * 25)
        vel[:] -= boundary * 10  # fine line of convergence

        # Dual-pol heuristics: hail cores, ZDR arcs, etc.
        hail_mask = storm_core > 60
        zdr[hail_mask] -= 1.5  # hail makes ZDR small or negative
        cc[hail_mask] -= 0.15
        kdp[hail_mask] += 2.5
        sw[hail_mask] += 3.0

        warm_rain = (storm_core > 30) & (storm_core < 55)
        zdr[warm_rain] += 0.8
        kdp[warm_rain] += 1.0

        # Spectrum width boosts where velocity gradients are strong.
        shear = np.abs(np.gradient(vel_field.reshape(self.grid_height, self.grid_width))[0])
        sw[:] += shear * 0.05

        # Velocity folding when magnitudes exceed Nyquist; this is purposely dramatic.
        folded = np.sin(vel / self.nyquist * math.pi)
        vel[:] = np.where(np.abs(vel) > self.nyquist, self.nyquist * folded, vel)

        # Correlation coefficient dips in debris or where noisy.
        cc[:] = np.clip(cc, 0.45, 1.02)
        zdr[:] = np.clip(zdr, -2.5, 6.0)
        kdp[:] = np.clip(kdp, -1.0, 7.5)
        sw[:] = np.clip(sw, 0.5, 12.0)

    def _apply_clutter(self, refl: np.ndarray) -> None:
        lon0, lat0 = self.radar_origin
        distance = self._distance_km(lon0, lat0, self.lon2d, self.lat2d)
        ring = np.exp(-((distance - self.clutter_ring_radius) ** 2) / (2 * 8 ** 2)) * 18
        refl[:] = np.maximum(refl, ring)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def _distance_km(self, lon1, lat1, lon2, lat2) -> np.ndarray:
        lon1_rad = np.radians(lon1)
        lat1_rad = np.radians(lat1)
        lon2_rad = np.radians(lon2)
        lat2_rad = np.radians(lat2)
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return self.earth_radius_km * c


__all__ = ["SyntheticStormModel", "StormCell", "RadarFrame"]
