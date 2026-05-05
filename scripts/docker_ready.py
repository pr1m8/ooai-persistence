"""Exit 0 when Docker responds quickly enough for Compose commands."""

from __future__ import annotations

import shutil
import subprocess
import sys


def main() -> int:
    docker = shutil.which("docker")
    if not docker:
        return 1
    try:
        result = subprocess.run(
            [docker, "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )
    except Exception:
        return 1
    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
