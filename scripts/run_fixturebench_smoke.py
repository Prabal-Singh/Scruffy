#!/usr/bin/env python3
"""Run FixtureBench against Scruffy's deterministic adapter (CI dogfood)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from fixturebench.cli import main as fb_main

    argv = [
        "run",
        "--agent",
        "scruffy.fixturebench_agent:ScruffyDeterministicAgent",
        "--tag",
        "smoke",
        *sys.argv[1:],
    ]
    return fb_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
