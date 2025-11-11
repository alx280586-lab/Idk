"""Minimal Torch-compatible API implemented with pure Python lists.

This stub covers only the subset of functionality needed by the FNC unit tests.
It is intentionally lightweight and does not support autograd or GPUs.
"""
from __future__ import annotations

import math
import pickle
import random
from contextlib import contextmanager
import builtins
from itertools import product
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

__all__ = [
    "Tensor",
    "tensor",
    "zeros",
    "ones",
    "linspace",
    "logspace",
    "randn",
    "randint",
    "stack",
    "meshgrid",
    "cat",
    "sin",
    "cos",
    "exp",
    "sqrt",
    "tanh",
    "softmax",
    "zeros_like",
    "prod",
    "clamp",
    "allclose",
    "relu",
    "manual_seed",
    "cuda",
    "nn",
    "optim",
    "no_grad",
    "float32",
    "long",
    "int64",
    "round",
]

float32 = "float32"
long = "long"
int64 = "int64"


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _infer_shape(data: Any) -> Tuple[int, ...]:
    if isinstance(data, Tensor):
        return data.shape
    if isinstance(data, (int, float)):
        return ()
    if isinstance(data, (list, tuple)):
        if not data:
            return (0,)
        first_shape = _infer_shape(data[0])
        for item in data:
            if _infer_shape(item) != first_shape:
                raise ValueError("Inconsistent shapes in nested data")
        return (len(data),) + first_shape
    raise TypeError(f"Unsupported data type: {type(data)!r}")


def _flatten(data: Any) -> List[float]:
    if isinstance(data, Tensor):
        return data._data[:]
    if isinstance(data, (int, float)):
        return [float(data)]
    if isinstance(data, (list, tuple)):
        flat: List[float] = []
        for item in data:
            flat.extend(_flatten(item))
        return flat
    raise TypeError(f"Unsupported data type: {type(data)!r}")


def _numel(shape: Tuple[int, ...]) -> int:
    total = 1
    for dim in shape:
        total *= dim
    return total


def _check_shape(data: List[float], shape: Tuple[int, ...]) -> None:
    if _numel(shape) != len(data):
        raise ValueError("Shape does not match data length")


def _broadcast_shapes(shape_a: Tuple[int, ...], shape_b: Tuple[int, ...]) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
    """Return broadcast result shape and padded input shapes."""

    max_dims = max(len(shape_a), len(shape_b))
    padded_a = (1,) * (max_dims - len(shape_a)) + shape_a
    padded_b = (1,) * (max_dims - len(shape_b)) + shape_b
    result: List[int] = []
    for dim_a, dim_b in zip(padded_a, padded_b):
        if dim_a == dim_b or dim_a == 1 or dim_b == 1:
            result.append(max(dim_a, dim_b))
        else:
            raise ValueError("Shapes are not broadcastable in stub")
    return tuple(result), padded_a, padded_b


def _index_flat(shape: Tuple[int, ...], index: Tuple[int, ...]) -> int:
    if len(index) != len(shape):
        raise IndexError("Invalid index length")
    flat_index = 0
    stride = 1
    for dim_size, idx in zip(reversed(shape), reversed(index)):
        if not 0 <= idx < dim_size:
            raise IndexError("Index out of range")
        flat_index += idx * stride
        stride *= dim_size
    return flat_index


def _unflatten(data: List[float], shape: Tuple[int, ...]) -> Any:
    if not shape:
        return data[0]
    if len(shape) == 1:
        return data[: shape[0]]
    step = _numel(shape[1:])
    return [
        _unflatten(data[i * step : (i + 1) * step], shape[1:])
        for i in range(shape[0])
    ]


def _apply_binary(a: "Tensor", b: "Tensor", op) -> "Tensor":
    if a.shape == b.shape:
        return Tensor([op(x, y) for x, y in zip(a._data, b._data)], shape=a.shape)
    if not a.shape:  # scalar broadcast
        return Tensor([op(a._data[0], y) for y in b._data], shape=b.shape)
    if not b.shape:
        return Tensor([op(x, b._data[0]) for x in a._data], shape=a.shape)
    result_shape, padded_a, padded_b = _broadcast_shapes(a.shape, b.shape)
    max_dims = len(result_shape)
    extra_a = max_dims - len(a.shape)
    extra_b = max_dims - len(b.shape)
    result = []
    for idx in product(*(range(s) for s in result_shape)):
        idx_a_padded = tuple(idx[d] if padded_a[d] > 1 else 0 for d in range(max_dims))
        idx_b_padded = tuple(idx[d] if padded_b[d] > 1 else 0 for d in range(max_dims))
        idx_a = idx_a_padded[extra_a:] if a.shape else ()
        idx_b = idx_b_padded[extra_b:] if b.shape else ()
        val_a = a._data[_index_flat(a.shape, idx_a)]
        val_b = b._data[_index_flat(b.shape, idx_b)]
        result.append(op(val_a, val_b))
    return Tensor(result, shape=result_shape)


def _apply_unary(a: "Tensor", op) -> "Tensor":
    return Tensor([op(x) for x in a._data], shape=a.shape)


def _index_recursive(data: Any, index: Any) -> Any:
    if isinstance(index, tuple):
        if not index:
            return data
        first, *rest = index
        return _index_recursive(data[first], tuple(rest))
    return data[index]


# ---------------------------------------------------------------------------
# Tensor implementation
# ---------------------------------------------------------------------------


class Tensor:
    def __init__(self, data: Any, shape: Optional[Tuple[int, ...]] = None) -> None:
        if shape is None:
            shape = _infer_shape(data)
        flat = _flatten(data)
        _check_shape(flat, shape)
        self._data = list(map(float, flat))
        self.shape = tuple(shape)
        self.requires_grad = False
        self.grad = None

    # Basic conversions -------------------------------------------------
    def clone(self) -> "Tensor":
        return Tensor(self._data, shape=self.shape)

    def detach(self) -> "Tensor":
        return self.clone()

    def item(self) -> float:
        if self.shape:
            raise ValueError("item() only supported for scalar tensors")
        return self._data[0]

    def tolist(self) -> Any:
        return _unflatten(self._data, self.shape)

    def backward(self) -> None:
        """Backpropagation stub: gradients are not supported."""

        return None

    # Casting and device (no-ops) --------------------------------------
    def to(self, device: Optional[str] = None):
        return self

    cpu = to

    def float(self) -> "Tensor":
        return self

    def long(self) -> "Tensor":
        return self

    @property
    def device(self) -> str:
        return "cpu"

    @property
    def dtype(self) -> str:
        return "float"

    # Shape utilities ---------------------------------------------------
    def numel(self) -> int:
        return len(self._data)

    nelement = numel

    def element_size(self) -> int:
        return 8

    def size(self, dim: Optional[int] = None):
        if dim is None:
            return self.shape
        dim = dim if dim >= 0 else dim + len(self.shape)
        return self.shape[dim]

    def dim(self) -> int:
        return len(self.shape)

    def view(self, *shape: int) -> "Tensor":
        shape = tuple(shape)
        if -1 in shape:
            known = [s for s in shape if s != -1]
            missing = int(self.numel() / max(1, _numel(tuple(known))))
            shape = tuple(missing if s == -1 else s for s in shape)
        _check_shape(self._data, shape)
        return Tensor(self._data, shape=shape)

    def reshape(self, *shape: int) -> "Tensor":
        return self.view(*shape)

    def unsqueeze(self, dim: int) -> "Tensor":
        dim = dim if dim >= 0 else dim + len(self.shape) + 1
        new_shape = list(self.shape)
        new_shape.insert(dim, 1)
        return Tensor(self._data, shape=tuple(new_shape))

    def squeeze(self, dim: Optional[int] = None) -> "Tensor":
        if dim is None:
            new_shape = tuple(s for s in self.shape if s != 1)
            if not new_shape:
                new_shape = (1,)
            return Tensor(self._data, shape=new_shape)
        dim = dim if dim >= 0 else dim + len(self.shape)
        if self.shape[dim] != 1:
            raise ValueError("Cannot squeeze dimension with size != 1")
        new_shape = list(self.shape)
        new_shape.pop(dim)
        return Tensor(self._data, shape=tuple(new_shape) or (1,))

    def expand(self, *shape: int) -> "Tensor":
        if len(shape) != len(self.shape):
            raise ValueError("expand in stub requires same rank")
        repeated = []
        for dim_size, target in zip(self.shape, shape):
            if dim_size not in (1, target):
                raise ValueError("Unsupported expand pattern in stub")
        data = self._data
        for dim_idx, (dim_size, target) in enumerate(zip(self.shape, shape)):
            if dim_size == target:
                continue
            repeats = target // dim_size
            block = []
            step = _numel(self.shape[dim_idx + 1 :]) or 1
            for i in range(0, len(data), step):
                block.extend(data[i : i + step] * repeats)
            data = block
        return Tensor(data, shape=tuple(shape))

    def transpose(self, dim0: int, dim1: int) -> "Tensor":
        dims = list(range(len(self.shape)))
        dim0 = dim0 if dim0 >= 0 else dim0 + len(dims)
        dim1 = dim1 if dim1 >= 0 else dim1 + len(dims)
        dims[dim0], dims[dim1] = dims[dim1], dims[dim0]
        return self.permute(*dims)

    def t(self) -> "Tensor":
        if len(self.shape) != 2:
            raise ValueError("t() only defined for 2D tensors in stub")
        rows, cols = self.shape
        matrix = self.tolist()
        transposed = [[matrix[j][i] for j in range(rows)] for i in range(cols)]
        return Tensor(transposed)

    def permute(self, *dims: int) -> "Tensor":
        if set(dims) != set(range(len(self.shape))):
            raise ValueError("Invalid permutation")
        new_shape = tuple(self.shape[d] for d in dims)
        new_data = [0.0] * _numel(new_shape)
        for old_indices in product(*(range(s) for s in self.shape)):
            value = self._data[_index_flat(self.shape, old_indices)]
            new_indices = tuple(old_indices[d] for d in dims)
            new_data[_index_flat(new_shape, new_indices)] = value
        return Tensor(new_data, shape=new_shape)

    # Reductions --------------------------------------------------------
    def mean(self, dim: Optional[int] = None, keepdim: bool = False) -> "Tensor":
        if dim is None:
            return Tensor(sum(self._data) / len(self._data))
        dim = dim if dim >= 0 else dim + len(self.shape)
        size = self.shape[dim]
        step = _numel(self.shape[dim + 1 :]) or 1
        outer = _numel(self.shape[:dim]) or 1
        result = []
        for i in range(outer):
            segment = []
            for j in range(size):
                start = (i * size + j) * step
                segment.extend(self._data[start : start + step])
            avg = sum(segment) / len(segment)
            result.append(avg)
        new_shape = list(self.shape)
        if keepdim:
            new_shape[dim] = 1
        else:
            new_shape.pop(dim)
        if not new_shape:
            return Tensor(result[0])
        return Tensor(result, shape=tuple(new_shape))

    def _reduce_var(self, dim: int, unbiased: bool, keepdim: bool) -> "Tensor":
        mean_tensor = self.mean(dim=dim, keepdim=True)
        diff = (self - mean_tensor).pow(2)
        denom = self.shape[dim] - (1 if unbiased else 0)
        denom = max(denom, 1)
        summed = diff.sum(dim=dim, keepdim=keepdim)
        return summed / Tensor(denom)

    def var(self, dim: Optional[int] = None, unbiased: bool = True, keepdim: bool = False) -> "Tensor":
        if dim is None:
            mean_val = self.mean().item()
            sq = sum((x - mean_val) ** 2 for x in self._data)
            denom = len(self._data) - (1 if unbiased else 0)
            denom = max(denom, 1)
            return Tensor(sq / denom)
        dim = dim if dim >= 0 else dim + len(self.shape)
        return self._reduce_var(dim, unbiased, keepdim)

    def std(self, dim: Optional[int] = None, unbiased: bool = True, keepdim: bool = False) -> "Tensor":
        var_tensor = self.var(dim=dim, unbiased=unbiased, keepdim=keepdim)
        return var_tensor.sqrt()

    def sum(self, dim: Optional[int] = None, keepdim: bool = False) -> "Tensor":
        if dim is None:
            return Tensor(sum(self._data))
        dim = dim if dim >= 0 else dim + len(self.shape)
        size = self.shape[dim]
        step = _numel(self.shape[dim + 1 :]) or 1
        outer = _numel(self.shape[:dim]) or 1
        result = []
        for i in range(outer):
            total = 0.0
            for j in range(size):
                start = (i * size + j) * step
                total += sum(self._data[start : start + step])
            result.append(total)
        new_shape = list(self.shape)
        if keepdim:
            new_shape[dim] = 1
        else:
            new_shape.pop(dim)
        if not new_shape:
            return Tensor(result[0])
        return Tensor(result, shape=tuple(new_shape))

    # Element-wise operations -------------------------------------------
    def __add__(self, other: Any) -> "Tensor":
        other = ensure_tensor(other, self.shape)
        return _apply_binary(self, other, lambda x, y: x + y)

    def __radd__(self, other: Any) -> "Tensor":
        return self.__add__(other)

    def __sub__(self, other: Any) -> "Tensor":
        other = ensure_tensor(other, self.shape)
        return _apply_binary(self, other, lambda x, y: x - y)

    def __rsub__(self, other: Any) -> "Tensor":
        other = ensure_tensor(other, self.shape)
        return _apply_binary(other, self, lambda x, y: x - y)

    def __mul__(self, other: Any) -> "Tensor":
        other = ensure_tensor(other, self.shape)
        return _apply_binary(self, other, lambda x, y: x * y)

    def __rmul__(self, other: Any) -> "Tensor":
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> "Tensor":
        other = ensure_tensor(other, self.shape)
        return _apply_binary(self, other, lambda x, y: x / y)

    def pow(self, exponent: float) -> "Tensor":
        return _apply_unary(self, lambda x: x**exponent)

    def sqrt(self) -> "Tensor":
        return _apply_unary(self, math.sqrt)

    def abs(self) -> "Tensor":
        return _apply_unary(self, abs)

    def round(self) -> "Tensor":
        return _apply_unary(self, builtins.round)

    def clamp(self, min: Optional[float] = None, max: Optional[float] = None) -> "Tensor":
        def _clamp(x: float) -> float:
            if min is not None and x < min:
                x = min
            if max is not None and x > max:
                x = max
            return x

        return _apply_unary(self, _clamp)

    def max(self) -> float:
        return max(self._data)

    def __getitem__(self, item):
        data = _index_recursive(self.tolist(), item)
        return Tensor(data)

    def new_tensor(self, data):
        return Tensor(data)

    def flatten(self) -> "Tensor":
        return Tensor(self._data, shape=(self.numel(),))

    def repeat(self, times: int) -> "Tensor":
        if len(self.shape) == 0:
            return Tensor([self.item()] * times, shape=(times,))
        if len(self.shape) == 1:
            return Tensor(self._data * times, shape=(self.shape[0] * times,))
        raise ValueError("repeat in stub only supports scalars or 1D tensors")

    def allclose(self, other: "Tensor", atol: float = 1e-6) -> bool:
        if self.shape != other.shape:
            return False
        return all(abs(x - y) <= atol for x, y in zip(self._data, other._data))

    def equal(self, other: "Tensor") -> bool:
        return self.allclose(other, atol=0.0)

    def argmax(self, dim: Optional[int] = None) -> "Tensor":
        if dim is None:
            idx = max(range(len(self._data)), key=lambda i: self._data[i])
            return Tensor(idx)
        dim = dim if dim >= 0 else dim + len(self.shape)
        axis_size = self.shape[dim]
        step = _numel(self.shape[dim + 1 :]) or 1
        outer = _numel(self.shape[:dim]) or 1
        indices = []
        for i in range(outer):
            best_idx = 0
            best_val = None
            for j in range(axis_size):
                start = (i * axis_size + j) * step
                val = sum(self._data[start : start + step])
                if best_val is None or val > best_val:
                    best_val = val
                    best_idx = j
            indices.append(best_idx)
        return Tensor(indices, shape=(len(indices),))

    # Matrix multiplication ---------------------------------------------
    def __matmul__(self, other: "Tensor") -> "Tensor":
        if len(self.shape) == 2 and len(other.shape) == 2:
            rows, inner = self.shape
            inner2, cols = other.shape
            if inner != inner2:
                raise ValueError("Incompatible shapes for matmul")
            a = self.tolist()
            b = other.tolist()
            result = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    val = sum(a[i][k] * b[k][j] for k in range(inner))
                    row.append(val)
                result.append(row)
            return Tensor(result)
        if len(self.shape) == 3 and len(other.shape) == 2:
            batch, rows, inner = self.shape
            inner2, cols = other.shape
            if inner != inner2:
                raise ValueError("Incompatible shapes for batched matmul")
            a = self.tolist()
            b = other.tolist()
            batch_result = []
            for b_idx in range(batch):
                block = []
                for i in range(rows):
                    row = []
                    for j in range(cols):
                        val = sum(a[b_idx][i][k] * b[k][j] for k in range(inner))
                        row.append(val)
                    block.append(row)
                batch_result.append(block)
            return Tensor(batch_result)
        if len(self.shape) == 3 and len(other.shape) == 3:
            batch, rows, inner = self.shape
            batch2, inner2, cols = other.shape
            if batch != batch2 or inner != inner2:
                raise ValueError("Incompatible shapes for batched matmul")
            a = self.tolist()
            b = other.tolist()
            batch_result = []
            for b_idx in range(batch):
                block = []
                for i in range(rows):
                    row = []
                    for j in range(cols):
                        val = sum(a[b_idx][i][k] * b[b_idx][k][j] for k in range(inner))
                        row.append(val)
                    block.append(row)
                batch_result.append(block)
            return Tensor(batch_result)
        raise ValueError("matmul in stub only supports 2D or simple batched 3D x 2D tensors")

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"Tensor(shape={self.shape}, data={self.tolist()!r})"


def ensure_tensor(value: Any, shape: Tuple[int, ...]) -> Tensor:
    if isinstance(value, Tensor):
        return value
    return Tensor([value] * _numel(shape), shape=shape)


def tensor(data: Any, dtype=None, device=None) -> Tensor:  # noqa: ARG001 - dtype/device unused
    if dtype in {int64, long}:
        if isinstance(data, (list, tuple)):
            converted = [int(x) for x in data]
        else:
            converted = int(data)
        return Tensor(converted)
    return Tensor(data)


def zeros(*shape: int, dtype=None) -> Tensor:  # noqa: ARG001 - dtype ignored
    return Tensor([0.0] * _numel(shape), shape=tuple(shape))


def ones(*shape: int, dtype=None) -> Tensor:  # noqa: ARG001 - dtype ignored
    return Tensor([1.0] * _numel(shape), shape=tuple(shape))


def zeros_like(other: Tensor) -> Tensor:
    return zeros(*other.shape)


def randn(*shape: int) -> Tensor:
    return Tensor([_rng.gauss(0.0, 1.0) for _ in range(_numel(shape))], shape=tuple(shape))


def randint(low: int, high: int, shape: Tuple[int, ...], generator=None) -> Tensor:  # noqa: D401 - match torch signature loosely
    del generator
    return Tensor([_rng.randrange(low, high) for _ in range(_numel(shape))], shape=tuple(shape))


_rng = random.Random(0)


def manual_seed(seed: int) -> None:
    _rng.seed(seed)


def linspace(start: float, end: float, steps: int) -> Tensor:
    steps = int(steps)
    if steps == 1:
        return Tensor([start])
    step = (end - start) / (steps - 1)
    return Tensor([start + i * step for i in range(steps)], shape=(steps,))


def logspace(start: float, end: float, steps: int, base: float = 10.0) -> Tensor:
    if steps == 1:
        return Tensor([base**start])
    step = (end - start) / (steps - 1)
    return Tensor([base ** (start + i * step) for i in range(steps)], shape=(steps,))


def stack(tensors: Sequence[Tensor], dim: int = 0) -> Tensor:
    tensors = [tensor(t) for t in tensors]
    if not tensors:
        raise ValueError("stack requires at least one tensor")
    base_shape = tensors[0].shape
    for t in tensors:
        if t.shape != base_shape:
            raise ValueError("All tensors must have same shape for stack")
    shape = list(base_shape)
    shape.insert(dim, len(tensors))
    data = []
    for t in tensors:
        data.extend(t._data)
    return Tensor(data, shape=tuple(shape))


def cat(tensors: Sequence[Tensor], dim: int = 0) -> Tensor:
    tensors = [tensor(t) for t in tensors]
    if dim != 0:
        raise NotImplementedError("cat stub only supports dim=0")
    data = []
    total = 0
    for t in tensors:
        data.extend(t._data)
        total += t.shape[0]
    return Tensor(data, shape=(total,))


def meshgrid(*tensors: Tensor, indexing: str = "ij") -> Tuple[Tensor, ...]:
    arrays = [t.tolist() for t in tensors]
    grids = _meshgrid(arrays, indexing=indexing)
    return tuple(Tensor(grid) for grid in grids)


def _meshgrid(arrays: List[List[float]], indexing: str = "ij") -> List[List[Any]]:
    if not arrays:
        return []
    from itertools import product

    grids = []
    for idx, arr in enumerate(arrays):
        grid = []
        for coords in product(*arrays):
            value = coords[idx if indexing == "ij" else (0 if idx == 1 else idx)]
            grid.append(value)
        grids.append(_reshape_list(grid, [len(a) for a in arrays]))
    return grids


def _reshape_list(data: List[Any], shape: List[int]) -> Any:
    if not shape:
        return data[0]
    if len(shape) == 1:
        return data[: shape[0]]
    step = 1
    for dim in shape[1:]:
        step *= dim
    return [
        _reshape_list(data[i * step : (i + 1) * step], shape[1:])
        for i in range(shape[0])
    ]


def sin(t: Tensor) -> Tensor:
    return _apply_unary(t, math.sin)


def cos(t: Tensor) -> Tensor:
    return _apply_unary(t, math.cos)


def exp(t: Tensor) -> Tensor:
    return _apply_unary(t, math.exp)


def sqrt(t: Tensor) -> Tensor:
    return _apply_unary(t, math.sqrt)


def tanh(t: Tensor) -> Tensor:
    return _apply_unary(t, math.tanh)


def softmax(t: Tensor, dim: int = -1) -> Tensor:
    dim = dim if dim >= 0 else dim + len(t.shape)
    axis_size = t.shape[dim]
    step = _numel(t.shape[dim + 1 :]) or 1
    outer = _numel(t.shape[:dim]) or 1
    data = t._data[:]
    for i in range(outer):
        # compute max for stability
        segment = []
        for j in range(axis_size):
            start = (i * axis_size + j) * step
            segment.extend(data[start : start + step])
        max_val = max(segment) if segment else 0.0
        exp_vals = [math.exp(x - max_val) for x in segment]
        total = sum(exp_vals) or 1.0
        norm_vals = [x / total for x in exp_vals]
        for j in range(len(norm_vals)):
            idx = (i * axis_size * step) + j
            data[idx] = norm_vals[j]
    return Tensor(data, shape=t.shape)


def save(obj: Any, path: str) -> None:
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load(path: str, map_location: Optional[str] = None) -> Any:  # noqa: ARG001
    with open(path, "rb") as f:
        return pickle.load(f)


@contextmanager
def no_grad():
    yield


class _CudaModule:
    def is_available(self) -> bool:
        return False

    def manual_seed_all(self, seed: int) -> None:  # pragma: no cover - compatibility
        manual_seed(seed)


cuda = _CudaModule()


class device(str):
    pass


# ---------------------------------------------------------------------------
# Neural network layers (extremely small subset)
# ---------------------------------------------------------------------------


class Parameter(Tensor):
    def __init__(self, data: Any, shape: Optional[Tuple[int, ...]] = None) -> None:
        super().__init__(data, shape=shape)
        self.requires_grad = True


class Module:
    def __init__(self) -> None:
        self._parameters: Dict[str, Parameter] = {}
        self._modules: Dict[str, Module] = {}

    def __setattr__(self, name: str, value: Any) -> None:
        if isinstance(value, Parameter):
            self._parameters[name] = value
        elif isinstance(value, Module):
            self._modules[name] = value
        object.__setattr__(self, name, value)

    def parameters(self) -> Iterator[Parameter]:
        for param in self._parameters.values():
            yield param
        for module in self._modules.values():
            yield from module.parameters()

    def state_dict(self, prefix: str = "") -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        for name, param in self._parameters.items():
            state[prefix + name] = param.tolist()
        for name, module in self._modules.items():
            state.update(module.state_dict(prefix + name + "."))
        return state

    def load_state_dict(self, state: Dict[str, Any], prefix: str = "") -> None:
        for name, param in self._parameters.items():
            key = prefix + name
            if key in state:
                self._parameters[name] = Parameter(state[key])
        for name, module in self._modules.items():
            module.load_state_dict(state, prefix + name + ".")

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    def forward(self, *args, **kwargs):  # pragma: no cover - interface
        raise NotImplementedError


class Linear(Module):
    def __init__(self, in_features: int, out_features: int, bias: bool = True) -> None:
        super().__init__()
        scale = 1.0 / max(1, in_features)
        weights = [(_rng.random() * 2 - 1) * scale for _ in range(in_features * out_features)]
        self.weight = Parameter(weights, shape=(in_features, out_features))
        self.bias = Parameter([(_rng.random() * 2 - 1) * scale for _ in range(out_features)]) if bias else None

    def forward(self, x: Tensor) -> Tensor:
        if len(x.shape) == 1:
            x = x.view(1, x.shape[0])
            squeezed = True
        else:
            squeezed = False
        out = x @ self.weight
        if self.bias is not None:
            bias_matrix = self.bias.view(1, self.bias.shape[0]).expand(*out.shape)
            out = out + bias_matrix
        if squeezed:
            out = out[0]
        return out


class ReLU(Module):
    def forward(self, x: Tensor) -> Tensor:
        return _apply_unary(x, lambda v: max(v, 0.0))


class SiLU(Module):
    def forward(self, x: Tensor) -> Tensor:
        def _silu(value: float) -> float:
            clamped = max(min(value, 20.0), -20.0)
            return value / (1.0 + math.exp(-clamped))

        return _apply_unary(x, _silu)


class Sequential(Module):
    def __init__(self, *modules: Module) -> None:
        super().__init__()
        self.modules = list(modules)

    def parameters(self) -> Iterator[Parameter]:
        for module in self.modules:
            yield from module.parameters()

    def state_dict(self, prefix: str = "") -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        for idx, module in enumerate(self.modules):
            state.update(module.state_dict(prefix + f"{idx}."))
        return state

    def load_state_dict(self, state: Dict[str, Any], prefix: str = "") -> None:
        for idx, module in enumerate(self.modules):
            module.load_state_dict(state, prefix + f"{idx}.")

    def forward(self, x: Tensor) -> Tensor:
        out = x
        for module in self.modules:
            out = module(out)
        return out


class Embedding(Module):
    def __init__(self, num_embeddings: int, embedding_dim: int) -> None:
        super().__init__()
        weights = [(_rng.random() * 2 - 1) * 0.1 for _ in range(num_embeddings * embedding_dim)]
        self.weight = Parameter(weights, shape=(num_embeddings, embedding_dim))

    def forward(self, indices: Tensor) -> Tensor:
        matrix = self.weight.tolist()
        idx_list = indices.tolist()
        if isinstance(idx_list[0], list):
            return Tensor([[matrix[int(i)] for i in row] for row in idx_list])
        return Tensor([matrix[int(i)] for i in idx_list])


class ModuleList(Module):
    def __init__(self, modules: Iterable[Module]) -> None:
        super().__init__()
        self.modules = list(modules)

    def __iter__(self):
        return iter(self.modules)

    def __getitem__(self, idx: int) -> Module:
        return self.modules[idx]

    def append(self, module: Module) -> None:
        self.modules.append(module)

    def parameters(self) -> Iterator[Parameter]:
        for module in self.modules:
            yield from module.parameters()

    def state_dict(self, prefix: str = "") -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        for idx, module in enumerate(self.modules):
            state.update(module.state_dict(prefix + f"{idx}."))
        return state

    def load_state_dict(self, state: Dict[str, Any], prefix: str = "") -> None:
        for idx, module in enumerate(self.modules):
            module.load_state_dict(state, prefix + f"{idx}.")


class Softmax(Module):
    def __init__(self, dim: int = -1) -> None:
        super().__init__()
        self.dim = dim

    def forward(self, x: Tensor) -> Tensor:
        return softmax(x, dim=self.dim)


class FunctionalNamespace:
    @staticmethod
    def pad(tensor: Tensor, pad: Sequence[int], mode: str = "constant", value: float = 0.0) -> Tensor:
        data = tensor.tolist()
        if len(pad) == 2:
            left, right = pad
            padded = [value] * left + data + [value] * right
            return Tensor(padded)
        if len(pad) == 4:
            l1, r1, l2, r2 = pad
            matrix = data
            padded_rows = [[value] * (len(matrix[0]) + l1 + r1) for _ in range(l2)]
            for row in matrix:
                padded_rows.append([value] * l1 + row + [value] * r1)
            padded_rows.extend([[value] * (len(matrix[0]) + l1 + r1) for _ in range(r2)])
            return Tensor(padded_rows)
        raise NotImplementedError("pad configuration not supported")

    @staticmethod
    def normalize(tensor: Tensor, p: int = 2, dim: int = 0, eps: float = 1e-12) -> Tensor:
        arr = tensor.tolist()
        norm = 0.0
        if dim == 0:
            norm = math.sqrt(sum(x**2 for x in arr))
            norm = max(norm, eps)
            return Tensor([x / norm for x in arr])
        raise NotImplementedError("normalize only supports dim=0 in stub")

    @staticmethod
    def mse_loss(input: Tensor, target: Tensor) -> Tensor:
        if input.shape != target.shape:
            raise ValueError("mse_loss requires matching shapes")
        diff = [(x - y) ** 2 for x, y in zip(input._data, target._data)]
        return Tensor(sum(diff) / len(diff))

    @staticmethod
    def cross_entropy(logits: Tensor, targets: Tensor) -> Tensor:
        probs = softmax(logits, dim=-1)
        target_idx = targets.tolist()
        logits_list = probs.tolist()
        losses = []
        for row, idx in zip(logits_list, target_idx):
            losses.append(-math.log(row[int(idx)] + 1e-9))
        return Tensor(sum(losses) / len(losses))

    @staticmethod
    def gelu(tensor: Tensor) -> Tensor:
        return _apply_unary(tensor, lambda x: 0.5 * x * (1.0 + math.erf(x / math.sqrt(2.0))))


class UtilsNamespace:
    @staticmethod
    def clip_grad_norm_(parameters: Iterable[Parameter], max_norm: float) -> float:
        return float(max_norm)


class NNNamespace:
    Module = Module
    Linear = Linear
    ReLU = ReLU
    SiLU = SiLU
    Sequential = Sequential
    Embedding = Embedding
    ModuleList = ModuleList
    Softmax = Softmax
    Parameter = Parameter
    functional = FunctionalNamespace
    utils = UtilsNamespace


nn = NNNamespace()


# ---------------------------------------------------------------------------
# Optimisers (no-op)
# ---------------------------------------------------------------------------


class _BaseOptim:
    def __init__(self, params: Iterable[Parameter], lr: float = 1e-3):
        self.params = list(params)
        self.lr = lr

    def zero_grad(self) -> None:
        for p in self.params:
            p.grad = None

    def step(self) -> None:
        pass


class OptimNamespace:
    class Adam(_BaseOptim):
        pass

    class AdamW(_BaseOptim):
        pass


optim = OptimNamespace()


# ---------------------------------------------------------------------------
# Additional helpers
# ---------------------------------------------------------------------------


def matmul(a: Tensor, b: Tensor) -> Tensor:
    return a @ b


def log(t: Tensor) -> Tensor:
    return _apply_unary(t, math.log)


def prod(t: Tensor) -> Tensor:
    total = 1.0
    for value in t._data:
        total *= value
    return Tensor(total)


def clamp(t: Tensor, min=None, max=None) -> Tensor:
    return t.clamp(min=min, max=max)


def relu(t: Tensor) -> Tensor:
    return _apply_unary(t, lambda x: max(x, 0.0))


def round(t: Tensor) -> Tensor:
    return t.round()


def allclose(a: Tensor, b: Tensor, atol: float = 1e-6) -> bool:
    return a.allclose(b, atol=atol)


# register submodules for import compatibility
import types
import sys

nn_module = types.ModuleType("torch.nn")
nn_module.Module = Module
nn_module.Linear = Linear
nn_module.ReLU = ReLU
nn_module.SiLU = SiLU
nn_module.Sequential = Sequential
nn_module.Embedding = Embedding
nn_module.ModuleList = ModuleList
nn_module.Softmax = Softmax
nn_module.Parameter = Parameter
nn_module.functional = FunctionalNamespace
nn_module.utils = UtilsNamespace
sys.modules[__name__ + ".nn"] = nn_module
functional_module = types.ModuleType("torch.nn.functional")
functional_module.pad = FunctionalNamespace.pad
functional_module.normalize = FunctionalNamespace.normalize
functional_module.mse_loss = FunctionalNamespace.mse_loss
functional_module.cross_entropy = FunctionalNamespace.cross_entropy
functional_module.gelu = FunctionalNamespace.gelu
sys.modules[__name__ + ".nn.functional"] = functional_module
utils_module = types.ModuleType("torch.nn.utils")
utils_module.clip_grad_norm_ = UtilsNamespace.clip_grad_norm_
sys.modules[__name__ + ".nn.utils"] = utils_module

optim_module = types.ModuleType("torch.optim")
optim_module.Adam = OptimNamespace.Adam
optim_module.AdamW = OptimNamespace.AdamW
optim_module.Optimizer = _BaseOptim
sys.modules[__name__ + ".optim"] = optim_module

