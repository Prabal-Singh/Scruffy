import pytest

from scruffy.browser.scraper import login_to_buyer_portal, scrape_buyer_po
from scruffy.browser.buyer_portal import open_po_from_orders
from scruffy.models.po import RawPurchaseOrder


@pytest.mark.browser
@pytest.mark.portal
def test_scrape_po_1042_matches_golden_v3(
    buyer_portal_v3_url: str, expected_po_1042_v3: dict
) -> None:
    po = scrape_buyer_po(buyer_portal_v3_url, "PO-1042")
    assert po == RawPurchaseOrder.model_validate(expected_po_1042_v3)


@pytest.mark.browser
@pytest.mark.portal
def test_po_1042_not_on_first_page(buyer_portal_v3_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        login_to_buyer_portal(page, buyer_portal_v3_url)
        assert page.locator("[data-testid='po-link-PO-1042']").count() == 0
        assert page.locator("[data-testid='orders-page-info']").inner_text() == "Page 1 of 3"


@pytest.mark.browser
@pytest.mark.portal
def test_open_po_from_orders_paginates(buyer_portal_v3_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        login_to_buyer_portal(page, buyer_portal_v3_url)
        open_po_from_orders(page, "PO-1042")
        assert page.locator("[data-testid='po-number']").inner_text() == "PO-1042"
