"""Unit tests for the virtual parameter vault."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from eidolon_prime.parameter_vault import ParameterVault


class ParameterVaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_vault_scales_to_billions_without_large_files(self) -> None:
        vault_path = self._tmpdir / "vault"
        vault = ParameterVault(
            str(vault_path), shard_size=25_000_000, virtualization_factor=2_048
        )
        target = 2_000_000_000
        vault.ensure_capacity(target)
        self.assertGreaterEqual(
            vault.total_parameters(),
            target,
            "Vault should represent billions of logical parameters.",
        )
        # Ensure the on-disk footprint remains tiny relative to the logical size.
        total_bytes = sum(file.stat().st_size for file in vault_path.glob("*.bin"))
        self.assertLess(
            total_bytes,
            10_000_000,
            "Virtualized parameter shards should remain lightweight on disk.",
        )
        sample = vault.sample_vector(6)
        self.assertEqual(len(sample), 6)
        self.assertTrue(all(isinstance(value, float) for value in sample))


if __name__ == "__main__":
    unittest.main()
