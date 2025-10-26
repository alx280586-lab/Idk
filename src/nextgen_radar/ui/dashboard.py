"""Declarative UI composition for the radar dashboard."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..rendering.engine import OverlayState


@dataclass(slots=True)
class ControlOption:
    label: str
    value: str


@dataclass(slots=True)
class DashboardContext:
    title: str
    products: Dict[str, str]
    selected_product: str
    tilts: List[float]
    ranges: List[int]
    smoothing_levels: List[float]
    overlay: OverlayState
    warnings_count: Dict[str, int] = field(default_factory=dict)


class DashboardRenderer:
    """Render the control dashboard using Jinja2 templates."""

    def __init__(self, template_dir: Path) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html']),
            enable_async=True,
        )

    async def render(self, context: DashboardContext) -> str:
        template = self.env.get_template('dashboard.html')
        return await template.render_async(
            title=context.title,
            products=context.products,
            selected_product=context.selected_product,
            tilts=context.tilts,
            ranges=context.ranges,
            smoothing_levels=context.smoothing_levels,
            overlay=context.overlay,
            warnings_count=context.warnings_count,
            warnings_json=json.dumps(context.warnings_count),
        )
