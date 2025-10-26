"""Multi-scale Gaussian smoothing for radar data."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Sequence

import numpy as np
import xarray as xr


def gaussian_kernel(size: int, sigma: float) -> np.ndarray:
    """Generate a 2D Gaussian kernel normalized to 1."""

    ax = np.linspace(-(size - 1) / 2.0, (size - 1) / 2.0, size)
    kernel = np.exp(-0.5 * (np.square(ax)[:, None] + np.square(ax)[None, :]) / sigma**2)
    kernel_sum = kernel.sum()
    if kernel_sum != 0:
        kernel /= kernel_sum
    return kernel.astype(np.float32)


@lru_cache(maxsize=16)
def precomputed_kernels(scales: Sequence[float], base_sizes: Sequence[int]) -> Sequence[np.ndarray]:
    kernels = []
    for sigma, base in zip(scales, base_sizes):
        size = max(int(base * sigma), 3) | 1
        kernels.append(gaussian_kernel(size, sigma))
    return tuple(kernels)


def convolve2d(data: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Apply convolution using FFT for large kernels and direct method for small ones."""

    if max(kernel.shape) > 9:
        shape = np.array(data.shape) + np.array(kernel.shape) - 1
        fft_data = np.fft.rfftn(data, shape)
        fft_kernel = np.fft.rfftn(kernel, shape)
        convolved = np.fft.irfftn(fft_data * fft_kernel, shape)
        start = [(k - 1) // 2 for k in kernel.shape]
        end = [start[dim] + data.shape[dim] for dim in range(2)]
        return convolved[start[0]:end[0], start[1]:end[1]]
    else:
        pad_h, pad_w = kernel.shape[0] // 2, kernel.shape[1] // 2
        padded = np.pad(data, ((pad_h, pad_h), (pad_w, pad_w)), mode="edge")
        result = np.zeros_like(data, dtype=np.float32)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                window = padded[i:i + kernel.shape[0], j:j + kernel.shape[1]]
                result[i, j] = np.sum(window * kernel)
        return result


def multiscale_gaussian_smoothing(
    data: xr.DataArray,
    scales: Sequence[float] = (0.5, 1.5, 3.0),
    base_sizes: Sequence[int] = (3, 5, 9),
    weights: Sequence[float] = (0.5, 0.35, 0.15),
) -> xr.DataArray:
    """Smooth a radar sweep using a weighted sum of Gaussian filters."""

    if len(scales) != len(base_sizes) or len(scales) != len(weights):
        raise ValueError("scales, base_sizes, and weights must have the same length")
    kernels = precomputed_kernels(tuple(scales), tuple(base_sizes))
    smoothed = np.zeros_like(data.values, dtype=np.float32)
    for kernel, weight in zip(kernels, weights):
        smoothed += weight * convolve2d(data.values, kernel)
    result = xr.DataArray(smoothed, dims=data.dims, coords=data.coords, attrs=data.attrs)
    result.attrs["smoothing"] = "multiscale_gaussian"
    return result


def adaptive_smoothing(
    data: xr.DataArray,
    textures: Iterable[xr.DataArray],
    texture_threshold: float = 0.4,
) -> xr.DataArray:
    """Blend original and smoothed data based on texture magnitude."""

    gradients = [np.gradient(texture.values) for texture in textures]
    magnitude = sum(np.hypot(gx, gy) for gx, gy in gradients) / max(len(gradients), 1)
    normalized = (magnitude - magnitude.min()) / (magnitude.ptp() + 1e-6)
    smooth = multiscale_gaussian_smoothing(data)
    blended = np.where(normalized > texture_threshold, data.values, smooth.values)
    return xr.DataArray(blended, dims=data.dims, coords=data.coords, attrs=data.attrs)
