"""Inference utilities for FNC."""

from .generate import main as generate_main
from .serve import main as serve_main

__all__ = ["generate_main", "serve_main"]
