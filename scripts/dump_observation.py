#!/usr/bin/env python3
"""Dump a compact page observation JSON — no LLM required.

Examples:
    python portals/v1/server.py   # terminal 1

    python scripts/dump_observation.py --page login
    python scripts/dump_observation.py --page orders
    python scripts/dump_observation.py --page po --po PO-1042
    python scripts/dump_observation.py --page po --po PO-1042 --headed
"""

from __future__ import annotations

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scruffy.browser.config import BrowserConfig
from scruffy.browser.observation import capture_page_observation
from scruffy.browser.runner import BrowserRunner
from scruffy.browser.scraper import DEFAULT_EMAIL, DEFAULT_PASSWORD, login_to_buyer_portal

DEFAULT_URL = "http://127.0.0.1:8000"


def navigate_to_page(page, portal_url: str, page_name: str, po_number: str | None) -> None:
    base = portal_url.rstrip("/")
    if page_name == "login":
        page.goto(f"{base}/login")
        return

    login_to_buyer_portal(page, portal_url, DEFAULT_EMAIL, DEFAULT_PASSWORD)

    if page_name == "orders":
        return

    if page_name == "po":
        if not po_number:
            raise SystemExit("--po is required when --page po")
        page.locator(f"[data-testid='po-link-{po_number}']").click()
        page.wait_for_url(f"**/orders/{po_number}")
        return

    raise SystemExit(f"Unknown page: {page_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dump browser page observation as JSON")
    parser.add_argument("--url", default=DEFAULT_URL, help="Portal base URL")
    parser.add_argument(
        "--page",
        choices=["login", "orders", "po"],
        default="orders",
        help="Which page to observe",
    )
    parser.add_argument("--po", help="PO number when --page po")
    parser.add_argument("--headed", action="store_true", help="Run browser headed")
    parser.add_argument("--max-text", type=int, default=4000, help="Max visible_text chars")
    args = parser.parse_args()

    runner = BrowserRunner(BrowserConfig(headless=not args.headed))
    with runner.session() as (_pw, _browser, _context, page):
        navigate_to_page(page, args.url, args.page, args.po)
        observation = capture_page_observation(page, max_text_length=args.max_text)

    print(json.dumps(observation.model_dump(), indent=2))


if __name__ == "__main__":
    main()
