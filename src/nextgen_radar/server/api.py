"""FastAPI application exposing radar services."""

from __future__ import annotations



import asyncio
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import ORJSONResponse, Response

from ..config import DataSourceConfig, ProductConfig, RadarConfig
from ..data.decoder import RadarDecoder, RadarVolume
from ..data.sources import HttpRadarSource, RadarFrame
from ..processing.analysis import StormSummary, summarize_storms
from ..processing.smoothing import multiscale_gaussian_smoothing
from ..products.base import build_default_products, derived_products
from ..rendering.engine import RadarRenderingEngine
from PIL import Image
from io import BytesIO


class RadarRegistry:
    """Manage stateful services for radar products."""

    def __init__(self, config: RadarConfig) -> None:
        self.config = config
        self.decoder = RadarDecoder()
        self.rendering = RadarRenderingEngine(config.rendering)
        self.products: Dict[str, ProductConfig] = config.products
        self.sources = [HttpRadarSource(source) for source in config.data_sources]
        self.history: Dict[str, List[RadarVolume]] = {}
        self.summary: Optional[StormSummary] = None
        self._lock = asyncio.Lock()

    async def ingest_frame(self, frame: RadarFrame) -> RadarVolume:
        volume = self.decoder.decode(frame)
        product_list = self.history.setdefault(volume.product, [])
        product_list.append(volume)
        if len(product_list) > self.config.rendering.frame_cache_size:
            del product_list[0]
        smoothed = multiscale_gaussian_smoothing(volume.sweep)
        derived = derived_products({volume.product: smoothed})
        for key, data in derived.items():
            self.rendering.render_volume(key, data)
        texture = self.rendering.render_volume(volume.product, smoothed)
        _ = texture  # placeholder for GPU upload
        warnings = self.summary.warnings if self.summary else []
        self.rendering.update_overlay(summarize_storms({volume.product: smoothed}, warnings))
        return volume

    async def update_summary(self, summary: StormSummary) -> None:
        async with self._lock:
            self.summary = summary
            self.rendering.update_overlay(summary)


async def get_registry(config: RadarConfig = Depends(lambda: default_config())) -> RadarRegistry:
    return RadarRegistry(config)


def default_config() -> RadarConfig:
    storage = Path("./data")
    storage.mkdir(exist_ok=True)
    products = {key: ProductConfig(product_id=key, display_name=prod.display_name, default_colormap=prod.colormap) for key, prod in build_default_products().items()}
    sources = [
        DataSourceConfig(
            identifier="nexrad",
            url="https://example.com/radar",
            products=list(products.keys()),
        )
    ]
    return RadarConfig(storage_dir=storage, data_sources=sources, products=products)


def create_app(config: Optional[RadarConfig] = None) -> FastAPI:
    app = FastAPI(default_response_class=ORJSONResponse)
    app.state.registry = RadarRegistry(config or default_config())

    @app.get("/products")
    async def list_products() -> Dict[str, dict]:
        return {
            product_id: {
                "display_name": product.display_name,
                "colormap": product.default_colormap,
            }
            for product_id, product in app.state.registry.products.items()
        }

    @app.get("/frames/{product}")
    async def get_frames(product: str, limit: int = 12) -> List[dict]:
        volumes = app.state.registry.history.get(product.upper())
        if not volumes:
            raise HTTPException(status_code=404, detail="No frames available")
        return [volume.to_json() for volume in volumes[-limit:]]

    @app.post("/summary")
    async def post_summary(summary: StormSummary) -> dict:
        await app.state.registry.update_summary(summary)
        return {"status": "ok"}

    @app.get("/overlay")
    async def overlay_state() -> dict:
        overlay = app.state.registry.rendering.overlay_summary()
        return {
            "warnings": overlay.warnings,
            "highest": overlay.highest_warning,
            "counts": overlay.counts,
        }

    @app.get("/textures/{product}")
    async def textures(product: str) -> Response:
        texture = app.state.registry.rendering.latest_frame(product.upper())
        if texture is None:
            raise HTTPException(status_code=404, detail="No texture available")
        image = Image.fromarray(texture, mode="RGBA")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return Response(buffer.getvalue(), media_type="image/png")

    return app


__all__ = ["create_app", "default_config", "RadarRegistry"]
