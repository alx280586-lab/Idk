"""Render the radar dashboard with mock data for prototyping."""

from __future__ import annotations

import asyncio
from pathlib import Path

from nextgen_radar.rendering.engine import OverlayState
from nextgen_radar.ui.dashboard import DashboardContext, DashboardRenderer


def main() -> None:
    overlay = OverlayState(
        warnings=["TOR (Confirmed)", "SVR (Observed)"],
        highest_warning="TOR - Confirmed",
    )
    context = DashboardContext(
        title="NextGen Radar",
        products={
            "REF": "Reflectivity",
            "VEL": "Velocity",
            "CC": "Correlation Coefficient",
            "ZDR": "Differential Reflectivity",
        },
        selected_product="REF",
        tilts=[0.5, 0.9, 1.5, 2.4],
        ranges=[60, 120, 248],
        smoothing_levels=[0.25, 0.5, 0.75, 1.0],
        overlay=overlay,
        warnings_count={"TOR": 2, "SVR": 1},
    )

    renderer = DashboardRenderer(Path("templates"))
    html = asyncio.run(renderer.render(context))
    output = Path("build/dashboard.html")
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(html)
    print(f"Dashboard rendered to {output}")


if __name__ == "__main__":
    main()
