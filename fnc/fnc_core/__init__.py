"""Core utilities for Fractal Neural Compression."""

from .config import FNCConfig
from .seeds import SeedRegistry
from .tensor_coords import CoordinateEncoder
from .precision import PrecisionPolicy
from .caching import CacheInterface, SimpleCache

__all__ = [
    "FNCConfig",
    "SeedRegistry",
    "CoordinateEncoder",
    "PrecisionPolicy",
    "CacheInterface",
    "SimpleCache",
]
