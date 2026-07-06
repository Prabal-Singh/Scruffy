import pytest

from scruffy.browser.scraper import scrape_buyer_po
from scruffy.models.po import RawPurchaseOrder


@pytest.mark.browser
@pytest.mark.portal
def test_scrape_po_1042_matches_golden(buyer_portal_url: str, expected_po_1042: dict) -> None:
    po = scrape_buyer_po(buyer_portal_url, "PO-1042")
    assert po == RawPurchaseOrder.model_validate(expected_po_1042)


@pytest.mark.browser
@pytest.mark.portal
def test_scrape_po_1042_line_count(buyer_portal_url: str) -> None:
    po = scrape_buyer_po(buyer_portal_url, "PO-1042")
    assert len(po.lines) == 3
    assert po.lines[0].raw_description == "Sweet-Disk"
    assert po.lines[0].raw_sku == "SWT-DSK"


@pytest.mark.browser
@pytest.mark.portal
def test_login_required_for_orders(buyer_portal_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        page.goto(f"{buyer_portal_url}/orders")
        page.wait_for_url("**/login")
