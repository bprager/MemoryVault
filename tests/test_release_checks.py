from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoryvault.release_checks import ReleaseConsistencyError, ensure_version_sync, read_latest_release_version


class ReleaseCheckTests(unittest.TestCase):
    def test_ensure_version_sync_accepts_matching_latest_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "pyproject.toml").write_text(
                '[project]\nname = "memoryvault"\nversion = "0.3.0"\n',
                encoding="utf-8",
            )
            (temp_path / "Chaneglog.md").write_text(
                "# Changelog\n\n## [Unreleased]\n\n## [0.3.0] - 2026-03-24\n",
                encoding="utf-8",
            )

            version = ensure_version_sync(temp_path / "pyproject.toml", temp_path / "Chaneglog.md")

            self.assertEqual(version, "0.3.0")

    def test_ensure_version_sync_rejects_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "pyproject.toml").write_text(
                '[project]\nname = "memoryvault"\nversion = "0.4.0"\n',
                encoding="utf-8",
            )
            (temp_path / "Chaneglog.md").write_text(
                "# Changelog\n\n## [Unreleased]\n\n## [0.3.0] - 2026-03-24\n",
                encoding="utf-8",
            )

            with self.assertRaises(ReleaseConsistencyError):
                ensure_version_sync(temp_path / "pyproject.toml", temp_path / "Chaneglog.md")

    def test_read_latest_release_version_skips_unreleased(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            changelog_path = Path(temp_dir) / "Chaneglog.md"
            changelog_path.write_text(
                "# Changelog\n\n## [Unreleased]\n\n## [0.3.1] - 2026-03-24\n\n## [0.3.0] - 2026-03-23\n",
                encoding="utf-8",
            )

            version = read_latest_release_version(changelog_path)

            self.assertEqual(version, "0.3.1")


if __name__ == "__main__":
    unittest.main()
