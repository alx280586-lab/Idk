from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from nextgen_radar.config import DataSourceConfig, ProductConfig, RadarConfig
from nextgen_radar.products.base import build_default_products
from nextgen_radar.server.api import create_app


def build_config(args: argparse.Namespace) -> RadarConfig:
    storage = Path(args.storage).expanduser()
    storage.mkdir(parents=True, exist_ok=True)
    product_defs = build_default_products()
    products = {
        key: ProductConfig(
            product_id=key,
            display_name=definition.display_name,
            default_colormap=definition.colormap,
            units=definition.units,
        )
        for key, definition in product_defs.items()
    }
    stations = [station.upper() for station in args.stations]
    data_sources = [
        DataSourceConfig(
            identifier="aws",
            kind="nexrad-aws",
            station=stations[0],
            stations=stations,
            request_interval=args.interval,
            archive_days=args.archive_days,
            products=list(products.keys()),
        )
    ]
    return RadarConfig(storage_dir=storage, data_sources=data_sources, products=products)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NextGen radar server with live NEXRAD ingest")
    parser.add_argument(
        "--station",
        "--stations",
        dest="stations",
        nargs="+",
        default=["KTLX"],
        help="One or more four-letter NEXRAD station IDs (e.g. KTLX KFDR)",
    )
    parser.add_argument("--storage", default="./data", help="Directory for cached radar volumes")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface for the API server")
    parser.add_argument("--port", type=int, default=8000, help="TCP port for the API server")
    parser.add_argument("--interval", type=float, default=75.0, help="Polling interval (seconds) for new Level II volumes")
    parser.add_argument("--archive-days", type=int, default=2, help="How many days back to search the AWS archive")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config(args)
    app = create_app(config)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
