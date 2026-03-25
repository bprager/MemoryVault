from __future__ import annotations

import re
from pathlib import Path


VERSION_PATTERN = re.compile(r'^version\s*=\s*"(?P<version>\d+\.\d+\.\d+)"\s*$')
CHANGELOG_RELEASE_PATTERN = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$")


class ReleaseConsistencyError(ValueError):
    """Raised when release metadata is missing or inconsistent."""


def read_project_version(pyproject_path: str | Path = "pyproject.toml") -> str:
    path = Path(pyproject_path)
    for line in path.read_text(encoding="utf-8").splitlines():
        match = VERSION_PATTERN.match(line.strip())
        if match:
            return match.group("version")
    raise ReleaseConsistencyError(f"project version not found in {path.as_posix()}")


def read_latest_release_version(changelog_path: str | Path = "Changelog.md") -> str:
    path = Path(changelog_path)
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CHANGELOG_RELEASE_PATTERN.match(line.strip())
        if match:
            return match.group("version")
    raise ReleaseConsistencyError(f"no released version entry found in {path.as_posix()}")


def ensure_version_sync(
    pyproject_path: str | Path = "pyproject.toml",
    changelog_path: str | Path = "Changelog.md",
) -> str:
    project_version = read_project_version(pyproject_path)
    changelog_version = read_latest_release_version(changelog_path)
    if project_version != changelog_version:
        raise ReleaseConsistencyError(
            "version mismatch: "
            f"pyproject.toml has {project_version} but {Path(changelog_path).as_posix()} has {changelog_version}"
        )
    return project_version
