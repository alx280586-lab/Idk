"""Geospatial utilities for overlay layers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
from pyproj import Transformer


@dataclass(slots=True)
class GeoLayer:
    name: str
    features: List[np.ndarray]
    crs: str


class GeoManager:
    """Load and manage geospatial overlay layers."""

    def __init__(self, data_dir: Path, target_crs: str = "EPSG:3857") -> None:
        self.data_dir = data_dir
        self.target_crs = target_crs
        self.transformers: Dict[str, Transformer] = {}
        self.layers: Dict[str, GeoLayer] = {}

    def load_layer(self, name: str, source_crs: str = "EPSG:4326") -> GeoLayer:
        if name in self.layers:
            return self.layers[name]
        path = self.data_dir / f"{name}.geojson"
        features: List[np.ndarray] = []
        if path.exists():
            import json

            content = json.loads(path.read_text())
            for feature in content.get("features", []):
                coords = feature["geometry"]["coordinates"]
                if feature["geometry"]["type"] == "Polygon":
                    features.append(self._transform_polygon(coords[0], source_crs))
                elif feature["geometry"]["type"] == "MultiPolygon":
                    for polygon in coords:
                        features.append(self._transform_polygon(polygon[0], source_crs))
        layer = GeoLayer(name=name, features=features, crs=self.target_crs)
        self.layers[name] = layer
        return layer

    def _transform_polygon(self, coords: Iterable[Tuple[float, float]], source_crs: str) -> np.ndarray:
        transformer = self._get_transformer(source_crs)
        points = np.array(list(coords))
        x, y = transformer.transform(points[:, 1], points[:, 0])
        return np.vstack([x, y]).T

    def _get_transformer(self, source_crs: str) -> Transformer:
        key = f"{source_crs}->{self.target_crs}"
        if key not in self.transformers:
            self.transformers[key] = Transformer.from_crs(source_crs, self.target_crs, always_xy=True)
        return self.transformers[key]
