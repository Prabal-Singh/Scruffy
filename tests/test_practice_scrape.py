import sys
from pathlib import Path

import pytest

# Allow running tests without install
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scruffy.browser.config import BrowserConfig
from scruffy.browser.extractors import extract_inventory_items
from scruffy.browser.runner import BrowserRunner

PRACTICE_URL = "https://www.saucedemo.com/"
PRACTICE_USER = "standard_user"
PRACTICE_PASS = "secret_sauce"


@pytest.fixture
def browser_runner(tmp_path: Path) -> BrowserRunner:
    return BrowserRunner(
        BrowserConfig(
            headless=True,
            screenshot_dir=tmp_path / "screenshots",
            trace_dir=tmp_path / "traces",
        )
    )


@pytest.mark.browser
def test_login_and_extract_inventory(browser_runner: BrowserRunner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        page.goto(PRACTICE_URL)
        page.locator("#user-name").fill(PRACTICE_USER)
        page.locator("#password").fill(PRACTICE_PASS)
        page.locator("#login-button").click()
        page.wait_for_url("**/inventory.html")

        items = extract_inventory_items(page)

    assert len(items) == 6
    assert all("name" in item and "price" in item for item in items)
    assert items[0]["name"] == "Sauce Labs Backpack"


@pytest.mark.browser
def test_screenshot_on_inventory_page(browser_runner: BrowserRunner, tmp_path: Path) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        page.goto(PRACTICE_URL)
        page.locator("#user-name").fill(PRACTICE_USER)
        page.locator("#password").fill(PRACTICE_PASS)
        page.locator("#login-button").click()
        page.wait_for_url("**/inventory.html")

        path = browser_runner.screenshot(page, "inventory")

    assert path is not None
    assert path.exists()
    assert path.stat().st_size > 0
