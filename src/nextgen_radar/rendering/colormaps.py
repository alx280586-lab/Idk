"""Colormap definitions for radar products."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


class ColorTable:
    """Represents a gradient colormap."""

    def __init__(self, name: str, stops: List[Tuple[float, Tuple[int, int, int, int]]]) -> None:
        self.name = name
        self.stops = sorted(stops, key=lambda stop: stop[0])
        self._stop_values = np.array([stop for stop, _ in self.stops], dtype=np.float32)
        self._color_values = np.array([color for _, color in self.stops], dtype=np.float32)

    def sample(self, value: float) -> Tuple[int, int, int, int]:
        value = np.clip(value, 0.0, 1.0)
        for idx, (stop, color) in enumerate(self.stops):
            if value <= stop:
                if idx == 0:
                    return color
                prev_stop, prev_color = self.stops[idx - 1]
                t = (value - prev_stop) / (stop - prev_stop + 1e-6)
                return tuple(int(prev_color[i] + t * (color[i] - prev_color[i])) for i in range(4))
        return self.stops[-1][1]

    def map_array(self, values: np.ndarray) -> np.ndarray:
        """Vectorized mapping for large radar grids."""

        clipped = np.clip(values, 0.0, 1.0)
        flat = clipped.reshape(-1)
        mapped = np.stack(
            [np.interp(flat, self._stop_values, self._color_values[:, channel]) for channel in range(4)],
            axis=-1,
        )
        return mapped.reshape((*clipped.shape, 4)).astype(np.uint8)


DEFAULT_TABLES: Dict[str, ColorTable] = {
    "reflectivity": ColorTable(
        "reflectivity",
        [
            (0.0, (0, 0, 0, 0)),
            (0.1, (0, 128, 255, 255)),
            (0.3, (0, 255, 0, 255)),
            (0.5, (255, 255, 0, 255)),
            (0.7, (255, 128, 0, 255)),
            (0.9, (255, 0, 0, 255)),
            (1.0, (255, 255, 255, 255)),
        ],
    ),
    "velocity": ColorTable(
        "velocity",
        [
            (0.0, (0, 0, 128, 255)),
            (0.33, (0, 255, 255, 255)),
            (0.66, (255, 255, 255, 255)),
            (1.0, (128, 0, 0, 255)),
        ],
    ),
    "correlation": ColorTable(
        "correlation",
        [
            (0.0, (128, 0, 128, 255)),
            (0.5, (255, 0, 255, 255)),
            (1.0, (255, 255, 255, 255)),
        ],
    ),
    "spectrum": ColorTable(
        "spectrum",
        [
            (0.0, (0, 0, 0, 255)),
            (1.0, (0, 255, 255, 255)),
        ],
    ),
    "zdr": ColorTable(
        "zdr",
        [
            (0.0, (0, 0, 0, 255)),
            (0.5, (255, 128, 0, 255)),
            (1.0, (255, 255, 255, 255)),
        ],
    ),
    "kdp": ColorTable(
        "kdp",
        [
            (0.0, (0, 0, 0, 255)),
            (0.5, (0, 255, 128, 255)),
            (1.0, (255, 255, 255, 255)),
        ],
    ),
    "vil": ColorTable(
        "vil",
        [
            (0.0, (0, 0, 0, 255)),
            (0.5, (0, 0, 255, 255)),
            (1.0, (255, 255, 255, 255)),
        ],
    ),
    "hail": ColorTable(
        "hail",
        [
            (0.0, (0, 0, 0, 255)),
            (1.0, (255, 0, 255, 255)),
        ],
    ),
}
