#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ruff check memoryvault tests scripts
if [ -x ".venv/bin/mypy" ]; then
  .venv/bin/mypy memoryvault tests
else
  python3 -m mypy memoryvault tests
fi
python3 scripts/markdown_lint.py README.md AGENTS.md Changelog.md docs .codex
python3 scripts/check_version_sync.py
python3 -m coverage erase
python3 -m coverage run -m unittest discover -s tests -v
python3 -m coverage report --fail-under=95 -m
