"""Radar data source interfaces for live and historical feeds."""

from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, Dict, Optional

import aiohttp
from cachetools import TTLCache

from ..config import DataSourceConfig


@dataclass(slots=True)
class RadarFrame:
    """Represents a single radar volume with metadata and payload."""

    product: str
    timestamp: dt.datetime
    elevation: float
    data: bytes
    station: str
    attributes: Dict[str, float]


class BaseRadarSource:
    """Base class for radar data sources."""

    def __init__(self, config: DataSourceConfig) -> None:
        self.config = config

    async def frames(self) -> AsyncGenerator[RadarFrame, None]:
        raise NotImplementedError


class HttpRadarSource(BaseRadarSource):
    """Stream radar frames from an HTTP endpoint."""

    def __init__(self, config: DataSourceConfig, session: Optional[aiohttp.ClientSession] = None) -> None:
        super().__init__(config)
        self._session = session
        self._cache: TTLCache[str, bytes] = TTLCache(maxsize=8, ttl=self.config.request_interval)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.request_interval)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def frames(self) -> AsyncGenerator[RadarFrame, None]:
        session = await self._get_session()
        while True:
            params = {"products": ",".join(self.config.products)} if self.config.products else None
            headers = {"Authorization": f"Bearer {self.config.auth_token}"} if self.config.auth_token else None
            async with session.get(self.config.url, params=params, headers=headers) as response:
                response.raise_for_status()
                payload = await response.read()
                cache_key = response.headers.get("ETag") or str(hash(payload))
                if cache_key in self._cache:
                    await asyncio.sleep(self.config.request_interval)
                    continue
                self._cache[cache_key] = payload
                metadata = {
                    "product": response.headers.get("X-Product", "UNKNOWN"),
                    "timestamp": response.headers.get("X-Timestamp"),
                    "elevation": response.headers.get("X-Elevation"),
                    "station": response.headers.get("X-Station", "UNK"),
                }
                yield RadarFrame(
                    product=metadata["product"],
                    timestamp=dt.datetime.fromisoformat(metadata["timestamp"]),
                    elevation=float(metadata["elevation"] or 0.5),
                    data=payload,
                    station=metadata["station"],
                    attributes={}
                )
            await asyncio.sleep(self.config.request_interval)

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()


class FileRadarSource(BaseRadarSource):
    """Load radar frames from a local archive for historical playback."""

    def __init__(self, config: DataSourceConfig, directory: Path) -> None:
        super().__init__(config)
        self.directory = directory

    async def frames(self) -> AsyncGenerator[RadarFrame, None]:
        for file in sorted(self.directory.glob("*.nexrad")):
            timestamp = dt.datetime.fromtimestamp(file.stat().st_mtime, tz=dt.timezone.utc)
            yield RadarFrame(
                product=self.config.products[0] if self.config.products else "UNKNOWN",
                timestamp=timestamp,
                elevation=0.5,
                data=file.read_bytes(),
                station=file.stem.split("_")[0],
                attributes={},
            )
            await asyncio.sleep(0)
