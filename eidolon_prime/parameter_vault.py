"""Virtualised parameter storage for ultra-large neural meshes."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional


@dataclass
class ParameterShard:
    """Describes a virtual shard of parameters backed by a lightweight file."""

    name: str
    size: int
    seed: int
    path: Path

    def descriptor(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "size": self.size,
            "seed": self.seed,
            "path": str(self.path),
        }


class ParameterVault:
    """Manages billions of virtual parameters without large memory footprints."""

    def __init__(
        self,
        root_path: str,
        *,
        shard_size: int = 50_000_000,
        virtualization_factor: int = 1_024,
    ) -> None:
        root = Path(root_path).expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        root.mkdir(parents=True, exist_ok=True)
        self._root = root
        self._metadata_path = self._root / "vault.json"
        self._shard_size = max(1, shard_size)
        self._virtualization_factor = max(1, virtualization_factor)
        self._shards: Dict[str, ParameterShard] = {}
        self._load_metadata()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_metadata(self) -> None:
        if not self._metadata_path.exists():
            return
        with self._metadata_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for descriptor in payload.get("shards", []):
            shard = ParameterShard(
                name=descriptor["name"],
                size=int(descriptor["size"]),
                seed=int(descriptor["seed"]),
                path=Path(descriptor["path"]),
            )
            self._shards[shard.name] = shard

    def _save_metadata(self) -> None:
        data = {
            "shards": [shard.descriptor() for shard in self._shards.values()],
            "virtualization_factor": self._virtualization_factor,
            "shard_size": self._shard_size,
        }
        with self._metadata_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ensure_capacity(self, target_parameters: int) -> None:
        """Ensure the vault represents at least ``target_parameters`` logical values."""

        logical_total = self.total_parameters()
        index = len(self._shards)
        while logical_total < target_parameters:
            shard_size = min(self._shard_size, target_parameters - logical_total)
            shard_name = f"shard-{index:06d}"
            shard_path = self._root / f"{shard_name}.bin"
            shard_seed = 73_379 + index * 97
            if not shard_path.exists():
                with shard_path.open("wb") as handle:
                    # Physical storage is scaled down by the virtualization factor.
                    handle.truncate(max(1, shard_size // self._virtualization_factor))
            shard = ParameterShard(shard_name, shard_size, shard_seed, shard_path)
            self._shards[shard_name] = shard
            logical_total += shard_size
            index += 1
        self._save_metadata()

    def total_parameters(self) -> int:
        return sum(shard.size for shard in self._shards.values())

    def shard_count(self) -> int:
        return len(self._shards)

    def sample_vector(self, length: int, *, seed: Optional[int] = None) -> List[float]:
        """Return a deterministic vector derived from the virtual shards."""

        if length <= 0:
            return []
        shards = list(self._shards.values())
        if not shards:
            # Guarantee a non-empty sample even before ensure_capacity is called.
            dummy_seed = 91_027
            shards = [
                ParameterShard(
                    name="virtual", size=self._shard_size, seed=dummy_seed, path=self._root
                )
            ]
        base_seed = seed or (sum(shard.seed for shard in shards) % 1_000_003)
        vector: List[float] = []
        for index in range(length):
            shard = shards[index % len(shards)]
            rng = random.Random(base_seed + shard.seed + index)
            amplitude = 1.0 + shard.size / max(1, self._shard_size)
            value = (rng.random() - 0.5) * 2.0 * amplitude
            vector.append(value)
        return vector

    def iter_chunks(self, chunk_size: int = 1024) -> Iterator[List[float]]:
        """Yield deterministic parameter chunks for streaming-based consumers."""

        if chunk_size <= 0:
            return
        for shard in self._shards.values():
            produced = 0
            while produced < shard.size:
                take = min(chunk_size, shard.size - produced)
                rng = random.Random(shard.seed + produced)
                chunk = [(rng.random() - 0.5) * 2.0 for _ in range(take)]
                yield chunk
                produced += take

    def metadata(self) -> Dict[str, object]:
        return {
            "root": str(self._root),
            "virtualization_factor": self._virtualization_factor,
            "shard_size": self._shard_size,
            "shards": [shard.descriptor() for shard in self._shards.values()],
        }


__all__ = ["ParameterVault", "ParameterShard"]
