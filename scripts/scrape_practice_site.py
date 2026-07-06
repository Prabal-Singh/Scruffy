#!/usr/bin/env python3
"""Phase 1 demo: log into a public practice site and extract inventory data.

Uses saucedemo.com — a stable site designed for automation practice.
Run with: python scripts/scrape_practice_site.py
"""

import json
import sys
from pathlib import Path

# Allow running without install
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scruffy.browser.config import BrowserConfig
from scruffy.browser.extractors import extract_inventory_items
from scruffy.browser.runner import BrowserRunner

PRACTICE_URL = "https://www.saucedemo.com/"
PRACTICE_USER = "standard_user"
PRACTICE_PASS = "secret_sauce"


def scrape_practice_inventory(*, headless: bool = True) -> list[dict[str, str]]:
    root = Path(__file__).resolve().parents[1]
    config = BrowserConfig(
        headless=headless,
        screenshot_dir=root / "screenshots",
        trace_dir=root / "test-results" / "traces",
    )
    runner = BrowserRunner(config)

    with runner.session() as (_pw, _browser, _context, page):
        page.goto(PRACTICE_URL)
        page.locator("#user-name").fill(PRACTICE_USER)
        page.locator("#password").fill(PRACTICE_PASS)
        page.locator("#login-button").click()
        page.wait_for_url("**/inventory.html")

        runner.screenshot(page, "inventory_page")
        items = extract_inventory_items(page)
        return items


def main() -> None:
    headless = "--headed" not in sys.argv
    items = scrape_practice_inventory(headless=headless)
    print(json.dumps(items, indent=2))
    print(f"\nExtracted {len(items)} items.")


if __name__ == "__main__":
    main()
