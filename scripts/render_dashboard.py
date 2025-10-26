"""Render the radar dashboard with live NWS warning overlays when available."""

from __future__ import annotations

import asyncio
from pathlib import Path
from collections import Counter

from nextgen_radar.rendering.engine import OverlayState
from nextgen_radar.ui.dashboard import DashboardContext, DashboardRenderer
from nextgen_radar.data.warnings import fetch_active_warnings


PRIORITY = {"TOR": 3, "SVR": 2, "FFW": 1, "SMW": 1}


async def build_overlay() -> OverlayState:
    warnings = await fetch_active_warnings(limit=20)
    overlay = OverlayState()
    overlay.warnings = [f"{warning.warning_type} ({warning.severity})" for warning in warnings]
    overlay.counts = dict(Counter(warning.warning_type for warning in warnings))
    if warnings:
        highest = max(warnings, key=lambda w: PRIORITY.get(w.warning_type, 0))
        overlay.highest_warning = f"{highest.warning_type} - {highest.severity}"
    return overlay


async def build_context() -> DashboardContext:
    overlay = await build_overlay()
    return DashboardContext(
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
        warnings_count=overlay.counts,
    )


def main() -> None:
    context = asyncio.run(build_context())
    renderer = DashboardRenderer(Path("templates"))
    html = asyncio.run(renderer.render(context))
    output = Path("build/dashboard.html")
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(html)
    print(f"Dashboard rendered to {output}")


if __name__ == "__main__":
    main()
