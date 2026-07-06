#!/usr/bin/env python3
"""Run the Phase 2 constrained browser agent against the fake buyer portal.

Terminal 1:
    python portals/v1/server.py

Terminal 2:
    python scripts/run_agent.py --headed
    python scripts/run_agent.py --goal "Open PO-1041" --headed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scruffy.agent.loop import run_agent
from scruffy.browser.scraper import DEFAULT_EMAIL, DEFAULT_PASSWORD
from scruffy.llm.client import OllamaError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "http://127.0.0.1:8000"
DEFAULT_GOAL = (
    f"Log into the buyer portal using email {DEFAULT_EMAIL} and password {DEFAULT_PASSWORD}. "
    "Open purchase order PO-1042 and finish when the PO line items are visible."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Scruffy constrained browser agent")
    parser.add_argument("--url", default=DEFAULT_URL, help="Portal base URL")
    parser.add_argument("--goal", default=DEFAULT_GOAL, help="Agent goal")
    parser.add_argument("--max-steps", type=int, default=12, help="Max ReAct iterations")
    parser.add_argument("--headed", action="store_true", help="Run browser headed")
    args = parser.parse_args()

    try:
        result = run_agent(
            args.url,
            args.goal,
            max_steps=args.max_steps,
            headless=not args.headed,
            screenshot_dir=ROOT / "screenshots",
            trace_dir=ROOT / "test-results" / "traces",
        )
    except OllamaError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("=== Agent trace ===")
    for step in result.steps:
        action = step.action
        print(
            f"[{step.step_number}] {step.url}\n"
            f"  action={action.action} target={action.target_id} text={action.text!r}\n"
            f"  reason={action.reason}\n"
            f"  -> {'OK' if step.success else 'FAIL'}: {step.message}"
        )

    print("\n=== Result ===")
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
