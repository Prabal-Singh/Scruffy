import pytest

from scruffy.browser.scraper import scrape_buyer_po
from scruffy.models.po import RawPurchaseOrder


@pytest.mark.browser
@pytest.mark.portal
def test_scrape_po_1042_matches_golden_v2(
    buyer_portal_v2_url: str, expected_po_1042_v2: dict
) -> None:
    po = scrape_buyer_po(buyer_portal_v2_url, "PO-1042")
    assert po == RawPurchaseOrder.model_validate(expected_po_1042_v2)


@pytest.mark.browser
@pytest.mark.portal
def test_scrape_po_1042_messy_uom_preserved(buyer_portal_v2_url: str) -> None:
    po = scrape_buyer_po(buyer_portal_v2_url, "PO-1042")
    units = [line.unit for line in po.lines]
    assert units == ["CASE", "each", "EA"]
