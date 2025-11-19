"""Infobox parsing placeholder."""
from __future__ import annotations

from typing import Dict
import re


def extract_infobox(text: str) -> Dict[str, str]:
    pattern = re.compile(r"\|(?P<key>[A-Za-z_ ]+)= (?P<value>.+)")
    return {m.group("key").strip(): m.group("value").strip() for m in pattern.finditer(text)}


__all__ = ["extract_infobox"]
