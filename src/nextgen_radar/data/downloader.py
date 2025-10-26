"""Utilities for downloading live NEXRAD volumes from NOAA's public S3 feed."""

from __future__ import annotations

import asyncio
import datetime as dt
import gzip
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiohttp


LOGGER = logging.getLogger(__name__)


S3_NAMESPACE = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


@dataclass(slots=True)
class NexradObject:
    """Represents a single object in the NEXRAD Level II AWS bucket."""

    key: str
    last_modified: dt.datetime
    size: int


@dataclass(slots=True)
class VolumeMetadata:
    """Parsed metadata extracted from the NEXRAD filename."""

    station: str
    timestamp: dt.datetime
    version: Optional[int]


class NexradAwsClient:
    """Minimal client for fetching latest Level II volumes from NOAA S3."""

    BASE_URL = "https://noaa-nexrad-level2.s3.amazonaws.com"

    def __init__(self, station: str, storage_dir: Path) -> None:
        self.station = station.upper()
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def latest_object(self, session: aiohttp.ClientSession, *, lookback_days: int = 2) -> Optional[NexradObject]:
        """Return the most recent object for the configured station."""

        now = dt.datetime.utcnow()
        for offset in range(lookback_days + 1):
            day = now - dt.timedelta(days=offset)
            prefix = f"{day:%Y/%m/%d}/{self.station}/"
            url = f"{self.BASE_URL}?list-type=2&max-keys=2000&prefix={prefix}"
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        LOGGER.debug("NEXRAD list request failed %s", response.status)
                        continue
                    payload = await response.text()
            except aiohttp.ClientError as exc:
                LOGGER.warning("Failed to list NEXRAD objects: %s", exc)
                continue
            try:
                root = ET.fromstring(payload)
            except ET.ParseError as exc:
                LOGGER.warning("Unable to parse AWS S3 listing XML: %s", exc)
                continue
            contents = root.findall("s3:Contents", S3_NAMESPACE)
            if not contents:
                continue
            def _parse_stamp(stamp: str) -> dt.datetime:
                cleaned = stamp.replace("Z", "+00:00")
                try:
                    return dt.datetime.fromisoformat(cleaned)
                except ValueError:
                    base = stamp.split(".")[0]
                    return dt.datetime.strptime(base, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)

            def _last_modified(element: ET.Element) -> dt.datetime:
                stamp = element.findtext("s3:LastModified", default="", namespaces=S3_NAMESPACE)
                return _parse_stamp(stamp)

            latest_element = max(contents, key=_last_modified)
            key = latest_element.findtext("s3:Key", default="", namespaces=S3_NAMESPACE)
            last_modified = latest_element.findtext("s3:LastModified", default="", namespaces=S3_NAMESPACE)
            size_text = latest_element.findtext("s3:Size", default="0", namespaces=S3_NAMESPACE)
            if not key:
                continue
            timestamp = _parse_stamp(last_modified)
            return NexradObject(key=key, last_modified=timestamp, size=int(size_text))
        return None

    async def download(self, session: aiohttp.ClientSession, obj: NexradObject) -> Path:
        """Download the object if it doesn't already exist locally."""

        local_path = self.storage_dir / Path(obj.key).name
        if local_path.exists():
            return self._ensure_decompressed(local_path)
        temp_path = local_path.with_suffix(local_path.suffix + ".part")
        try:
            async with self._lock:
                if local_path.exists():
                    return self._ensure_decompressed(local_path)
                LOGGER.info("Downloading %s", obj.key)
                async with session.get(f"{self.BASE_URL}/{obj.key}") as response:
                    response.raise_for_status()
                    with temp_path.open("wb") as handle:
                        async for chunk in response.content.iter_chunked(1 << 15):
                            handle.write(chunk)
                temp_path.rename(local_path)
        except aiohttp.ClientError as exc:
            LOGGER.error("Failed to download %s: %s", obj.key, exc)
            temp_path.unlink(missing_ok=True)
            raise
        return self._ensure_decompressed(local_path)

    def _ensure_decompressed(self, path: Path) -> Path:
        if path.suffix != ".gz":
            return path
        target = path.with_suffix("")
        if target.exists():
            return target
        LOGGER.debug("Decompressing %s", path.name)
        with gzip.open(path, "rb") as source, target.open("wb") as destination:
            destination.write(source.read())
        return target


FILENAME_PATTERN = re.compile(
    r"(?P<station>[A-Z0-9]{4})(?P<date>\d{8})_(?P<time>\d{6})_V(?P<version>\d{2})"
)


def parse_volume_metadata(path: Path) -> Optional[VolumeMetadata]:
    """Parse the volume metadata from a Level II filename."""

    match = FILENAME_PATTERN.search(path.name)
    if not match:
        return None
    date = match.group("date")
    time = match.group("time")
    timestamp = dt.datetime.strptime(f"{date}{time}", "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
    version = int(match.group("version")) if match.group("version") else None
    return VolumeMetadata(station=match.group("station"), timestamp=timestamp, version=version)


__all__ = ["NexradAwsClient", "NexradObject", "VolumeMetadata", "parse_volume_metadata"]

