"""FastAPI application exposing radar services."""

from __future__ import annotations



import asyncio
import logging
from collections import Counter
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import aiohttp
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, ORJSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
import xarray as xr

from ..config import DataSourceConfig, ProductConfig, RadarConfig
from ..data.decoder import RadarDecoder, RadarVolume
from ..data.sources import BaseRadarSource, HttpRadarSource, NexradAwsSource, RadarFrame
from ..data.warnings import fetch_active_warnings
from ..processing.analysis import StormSummary, summarize_storms
from ..processing.smoothing import multiscale_gaussian_smoothing
from ..products.base import build_default_products, derived_products
from ..rendering.engine import RadarRenderingEngine


class RadarRegistry:
    """Manage stateful services for radar products."""

    def __init__(self, config: RadarConfig) -> None:
        self.config = config
        self.decoder = RadarDecoder()
        self.rendering = RadarRenderingEngine(config.rendering)
        self.products: Dict[str, ProductConfig] = config.products
        self.sources = self._build_sources(config)
        self.history: Dict[str, List[RadarVolume]] = {}
        self.summary: Optional[StormSummary] = None
        self._lock = asyncio.Lock()
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._tasks: List[asyncio.Task] = []
        self._warning_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)

    def _build_sources(self, config: RadarConfig) -> List[BaseRadarSource]:
        sources = []
        for source_config in config.data_sources:
            if source_config.kind == "nexrad-aws":
                stations = []
                if source_config.station:
                    stations.append(source_config.station)
                stations.extend(source_config.stations)
                if not stations:
                    raise ValueError("NEXRAD AWS sources require at least one station code")
                seen = set()
                for station in stations:
                    if not station or station.upper() in seen:
                        continue
                    seen.add(station.upper())
                    identifier = source_config.identifier or "nexrad"
                    child_identifier = f"{identifier}-{station.lower()}"
                    child_config = replace(
                        source_config,
                        identifier=child_identifier,
                        station=station.upper(),
                        stations=[station.upper()],
                    )
                    storage = config.storage_dir / child_identifier
                    sources.append(NexradAwsSource(child_config, storage))
            else:
                sources.append(HttpRadarSource(source_config))
        return sources

    async def ingest_frame(self, frame: RadarFrame) -> List[RadarVolume]:
        volumes = self.decoder.decode(frame)
        field_payloads: Dict[str, xr.DataArray] = {}
        for volume in volumes:
            history = self.history.setdefault(volume.product, [])
            history.append(volume)
            if len(history) > self.config.rendering.frame_cache_size:
                del history[0]
            smoothed = multiscale_gaussian_smoothing(volume.sweep)
            self.rendering.render_volume(volume.product, smoothed)
            base_key = volume.product.split("_")[0]
            if base_key not in field_payloads or volume.product == base_key:
                field_payloads[base_key] = smoothed
            if volume.product != base_key:
                field_payloads[volume.product] = smoothed
        derived = derived_products(field_payloads)
        for key, data in derived.items():
            self.rendering.render_volume(key, data)
            field_payloads[key] = data
        warnings = self.summary.warnings if self.summary else []
        self.rendering.update_overlay(summarize_storms(field_payloads, warnings))
        return volumes

    async def update_summary(self, summary: StormSummary) -> None:
        async with self._lock:
            self.summary = summary
            self.rendering.update_overlay(summary)

    async def _get_http_session(self) -> aiohttp.ClientSession:
        if self._http_session is None:
            timeout = aiohttp.ClientTimeout(total=20)
            headers = {
                "User-Agent": "nextgen-radar/0.1 (mailto:alx280586@gmail.com)",
                "Accept": "application/geo+json",
            }
            self._http_session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._http_session

    async def fetch_warnings(
        self,
        *,
        zone: Optional[Sequence[str]] = None,
        area: Optional[str] = None,
        event: Optional[Sequence[str]] = None,
        point: Optional[Sequence[float]] = None,
        limit: int = 50,
    ) -> StormSummary:
        session = await self._get_http_session()
        warnings = await fetch_active_warnings(
            session=session,
            zone=zone,
            area=area,
            event=event,
            point=point,
            limit=limit,
        )
        summary = summarize_storms({}, warnings)
        await self.update_summary(summary)
        return summary

    async def start(self) -> None:
        if self._tasks:
            return
        for source in self.sources:
            self._tasks.append(asyncio.create_task(self._pump_source(source)))
        self._warning_task = asyncio.create_task(self._refresh_warnings())

    async def _pump_source(self, source: BaseRadarSource) -> None:
        try:
            async for frame in source.frames():
                try:
                    await self.ingest_frame(frame)
                except Exception as exc:  # pragma: no cover - runtime safety
                    self.logger.exception("Failed to ingest frame from %s: %s", source.config.identifier, exc)
        finally:
            await source.close()

    async def _refresh_warnings(self) -> None:
        while True:
            try:
                await self.fetch_warnings(limit=50)
            except Exception as exc:  # pragma: no cover - network safety
                self.logger.warning("Warning refresh failed: %s", exc)
            await asyncio.sleep(self.config.warning_refresh_interval)

    async def close(self) -> None:
        for task in self._tasks:
            task.cancel()
        if self._warning_task is not None:
            self._warning_task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        if self._warning_task is not None:
            await asyncio.gather(self._warning_task, return_exceptions=True)
        for source in self.sources:
            if hasattr(source, "close"):
                await source.close()  # type: ignore[func-returns-value]
        if self._http_session is not None:
            await self._http_session.close()


async def get_registry(config: RadarConfig = Depends(lambda: default_config())) -> RadarRegistry:
    return RadarRegistry(config)


def default_config() -> RadarConfig:
    storage = Path("./data")
    storage.mkdir(exist_ok=True)
    products = {key: ProductConfig(product_id=key, display_name=prod.display_name, default_colormap=prod.colormap) for key, prod in build_default_products().items()}
    sources = [
        DataSourceConfig(
            identifier="aws",
            kind="nexrad-aws",
            station="KTLX",
            stations=["KTLX"],
            products=list(products.keys()),
            request_interval=90.0,
        )
    ]
    return RadarConfig(storage_dir=storage, data_sources=sources, products=products)


def create_app(config: Optional[RadarConfig] = None) -> FastAPI:
    app = FastAPI(default_response_class=ORJSONResponse)
    app.state.registry = RadarRegistry(config or default_config())

    project_root = Path(__file__).resolve().parents[3]
    templates = Jinja2Templates(directory=str(project_root / "templates"))
    static_dir = project_root / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        registry: RadarRegistry = app.state.registry
        overlay = registry.rendering.overlay_summary()
        product_map = {
            product_id: registry.products[product_id].display_name or product_id
            for product_id in sorted(registry.products)
        }
        selected_product = next(iter(product_map)) if product_map else ""
        context = {
            "request": request,
            "title": "NextGen Radar",
            "products": product_map,
            "selected_product": selected_product,
            "tilts": [0.5, 0.9, 1.5, 2.4, 3.1],
            "ranges": [60, 120, 180, 248],
            "warnings_count": overlay.counts,
            "overlay": overlay,
            "api_base": str(request.base_url),
        }
        return templates.TemplateResponse("dashboard.html", context)

    @app.on_event("startup")
    async def _startup() -> None:
        await app.state.registry.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await app.state.registry.close()

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

    @app.get("/warnings")
    async def list_warnings(
        zone: Optional[str] = None,
        area: Optional[str] = None,
        event: Optional[str] = None,
        point: Optional[str] = None,
        limit: int = 50,
    ) -> dict:
        point_values: Optional[Sequence[float]] = None
        if point:
            try:
                lat_str, lon_str = point.split(",", 1)
                point_values = [float(lat_str.strip()), float(lon_str.strip())]
            except (ValueError, AttributeError):
                raise HTTPException(status_code=400, detail="point must be 'lat,lon'")
        summary = await app.state.registry.fetch_warnings(
            zone=zone.split(",") if zone else None,
            area=area,
            event=event.split(",") if event else None,
            point=point_values,
            limit=limit,
        )
        counts = dict(Counter(warning.warning_type for warning in summary.warnings))
        return {
            "warnings": [
                {
                    "type": warning.warning_type,
                    "severity": warning.severity,
                    "expires": warning.expires,
                    "polygon": warning.polygon,
                }
                for warning in summary.warnings
            ],
            "counts": counts,
            "highest": app.state.registry.rendering.overlay_state.highest_warning,
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

