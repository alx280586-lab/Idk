"""Configuration objects for the radar engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass(slots=True)
class ProductConfig:
    """Configuration for an individual radar product."""

    product_id: str
    display_name: str
    default_colormap: str
    smoothing_scales: Sequence[float] = (0.5, 1.5, 3.0)
    dynamic_range: Optional[Sequence[float]] = None
    units: Optional[str] = None
    opacity: float = 1.0


@dataclass(slots=True)
class DataSourceConfig:
    """Defines a remote or local data source providing radar volumes."""

    identifier: str
    url: str
    auth_token: Optional[str] = None
    request_interval: float = 90.0
    products: Sequence[str] = field(default_factory=list)


@dataclass(slots=True)
class RenderingConfig:
    """Rendering configuration for OpenGL/WebGL pipelines."""

    use_webgl: bool = True
    background_color: Sequence[float] = (0.0, 0.0, 0.0, 1.0)
    frame_cache_size: int = 24
    enable_gaussian_prefilter: bool = True
    gaussian_kernel_sizes: Sequence[int] = (3, 5, 9)
    enable_dynamic_downsampling: bool = True


@dataclass(slots=True)
class RadarConfig:
    """Global configuration for the radar engine."""

    storage_dir: Path
    data_sources: Sequence[DataSourceConfig]
    products: Dict[str, ProductConfig]
    rendering: RenderingConfig = field(default_factory=RenderingConfig)
    enable_mesocyclone_detection: bool = True
    enable_hook_echo_detection: bool = True
    enable_hail_probability: bool = True
    lightning_feed_url: Optional[str] = None
    geospatial_layers: Iterable[str] = field(
        default_factory=lambda: (
            "states",
            "counties",
            "roads",
            "rivers",
            "cities",
        )
    )

    def product_list(self) -> List[ProductConfig]:
        return [self.products[key] for key in sorted(self.products)]
