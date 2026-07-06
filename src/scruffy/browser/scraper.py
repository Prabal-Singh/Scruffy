from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page

from scruffy.browser.buyer_portal import extract_po_detail, open_po_from_orders
from scruffy.browser.config import BrowserConfig
from scruffy.browser.runner import BrowserRunner
from scruffy.models.po import RawPurchaseOrder

DEFAULT_EMAIL = "vendor@scruffy.test"
DEFAULT_PASSWORD = "scruffy123"


def login_to_buyer_portal(
    page: Page,
    portal_url: str,
    email: str = DEFAULT_EMAIL,
    password: str = DEFAULT_PASSWORD,
) -> None:
    page.goto(f"{portal_url.rstrip('/')}/login")
    page.locator("[data-testid='login-email']").fill(email)
    page.locator("[data-testid='login-password']").fill(password)
    page.locator("[data-testid='login-submit']").click()
    page.wait_for_url("**/orders")


def scrape_buyer_po(
    portal_url: str,
    po_number: str,
    *,
    email: str = DEFAULT_EMAIL,
    password: str = DEFAULT_PASSWORD,
    headless: bool = True,
    screenshot_dir: Path | None = None,
    trace_dir: Path | None = None,
) -> RawPurchaseOrder:
    runner = BrowserRunner(
        BrowserConfig(
            headless=headless,
            screenshot_dir=screenshot_dir,
            trace_dir=trace_dir,
        )
    )
    with runner.session() as (_pw, _browser, _context, page):
        login_to_buyer_portal(page, portal_url, email, password)
        open_po_from_orders(page, po_number)
        runner.screenshot(page, f"po_{po_number.replace('-', '_').lower()}")
        return extract_po_detail(page)
