"""Utilities for retrieving live NWS warning polygons."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Iterable, List, Optional

import aiohttp

from ..processing.analysis import StormWarning

NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"
DEFAULT_HEADERS = {
    "User-Agent": "nextgen-radar/0.1 (mailto:alx280586@gmail.com)",
    "Accept": "application/geo+json",
}


def _to_csv(value: Optional[Iterable[str]]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        return value.decode() if isinstance(value, bytes) else value
    items = [item for item in value if item]
    return ",".join(dict.fromkeys(items)) or None


async def fetch_active_warnings(
    session: Optional[aiohttp.ClientSession] = None,
    *,
    zone: Optional[Iterable[str]] = None,
    area: Optional[str] = None,
    event: Optional[Iterable[str]] = None,
    point: Optional[Sequence[float]] = None,
    limit: int = 50,
) -> List[StormWarning]:
    """Fetch active NWS warnings and polygons from api.weather.gov.

    Parameters
    ----------
    session:
        Optional :class:`aiohttp.ClientSession` to reuse connections.
    zone:
        Iterable of zone identifiers (for example, ``['ILZ013', 'ILZ014']``).
    area:
        NWS area identifier (``state`` or ``forecast office`` code).
    event:
        Iterable of event names (``['Tornado Warning', 'Severe Thunderstorm Warning']``).
    point:
        Optional latitude/longitude pair for spatial filtering.
    limit:
        Maximum number of alerts to return.
    """

    params = {"limit": str(limit)}
    zone_param = _to_csv(zone)
    event_param = _to_csv(event)
    if zone_param:
        params["zone"] = zone_param
    if area:
        params["area"] = area
    if event_param:
        params["event"] = event_param
    if point:
        params["point"] = f"{point[0]},{point[1]}"

    close_session = False
    if session is None:
        timeout = aiohttp.ClientTimeout(total=20)
        session = aiohttp.ClientSession(timeout=timeout)
        close_session = True

    try:
        async with session.get(NWS_ALERTS_URL, params=params, headers=DEFAULT_HEADERS) as response:
            response.raise_for_status()
            payload = await response.json()
    finally:
        if close_session:
            await session.close()

    warnings: List[StormWarning] = []
    for feature in payload.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry") or {}
        polygon: List[Sequence[float]] = []
        coordinates = geometry.get("coordinates") or []
        if geometry.get("type") == "Polygon" and coordinates:
            polygon = [
                (float(lat), float(lon))
                for lon, lat in coordinates[0]
            ]
        elif geometry.get("type") == "MultiPolygon" and coordinates:
            ring = coordinates[0][0]
            polygon = [(float(lat), float(lon)) for lon, lat in ring]

        warnings.append(
            StormWarning(
                warning_type=_simplify_event(properties.get("event")),
                severity=(properties.get("severity") or "Unknown"),
                expires=(properties.get("ends") or properties.get("expires") or ""),
                polygon=polygon,
            )
        )
    return warnings


def _simplify_event(event_name: Optional[str]) -> str:
    if not event_name:
        return "UNK"
    mapping = {
        "Tornado Warning": "TOR",
        "Severe Thunderstorm Warning": "SVR",
        "Flash Flood Warning": "FFW",
        "Special Marine Warning": "SMW",
    }
    return mapping.get(event_name, event_name.upper())


__all__ = ["fetch_active_warnings"]
