#!/usr/bin/env python3
"""Scrape a PO from the local fake buyer portal (portals/v1).

Start the portal first:
    python portals/v1/server.py

Then run:
    python scripts/scrape_buyer_portal.py
    python scripts/scrape_buyer_portal.py --headed
    python scripts/scrape_buyer_portal.py --po PO-1041 --url http://127.0.0.1:8000
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scruffy.browser.scraper import scrape_buyer_po

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "http://127.0.0.1:8000"


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape a PO from the fake buyer portal")
    parser.add_argument("--url", default=DEFAULT_URL, help="Portal base URL")
    parser.add_argument("--po", default="PO-1042", help="PO number to scrape")
    parser.add_argument("--headed", action="store_true", help="Run browser headed")
    args = parser.parse_args()

    po = scrape_buyer_po(
        args.url,
        args.po,
        headless=not args.headed,
        screenshot_dir=ROOT / "screenshots",
        trace_dir=ROOT / "test-results" / "traces",
    )
    print(json.dumps(po.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
