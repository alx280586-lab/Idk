from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AutomationSettings(BaseModel):
    enabled: bool
    daily_cap: Optional[int] = None
