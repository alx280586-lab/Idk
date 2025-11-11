"""Top-level package for the Fractal Neural Compression (FNC) project."""

from importlib import metadata

__all__ = ["__version__"]


def __getattr__(name: str):
    if name == "__version__":
        try:
            return metadata.version("fnc")
        except metadata.PackageNotFoundError:  # pragma: no cover - during dev
            return "0.0.0"
    raise AttributeError(name)
