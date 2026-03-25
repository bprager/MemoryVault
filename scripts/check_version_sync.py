#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main() -> int:
    from memoryvault.release_checks import ReleaseConsistencyError, ensure_version_sync

    try:
        version = ensure_version_sync()
    except ReleaseConsistencyError as error:
        print(str(error), file=sys.stderr)
        return 1

    print(f"release version sync ok: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
