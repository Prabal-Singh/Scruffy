import pytest

from scruffy.browser.observation import capture_page_observation
from scruffy.browser.scraper import login_to_buyer_portal
from scruffy.models.observation import PageObservation


@pytest.mark.browser
@pytest.mark.portal
def test_observation_login_page(buyer_portal_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        page.goto(f"{buyer_portal_url}/login")
        obs = capture_page_observation(page)

    assert obs.url.endswith("/login")
    assert obs.title
    assert any(e.test_id == "login-email" for e in obs.interactive_elements)
    assert any(e.test_id == "login-submit" for e in obs.interactive_elements)
    assert "Sign in" in obs.visible_text


@pytest.mark.browser
@pytest.mark.portal
def test_observation_orders_page(buyer_portal_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        login_to_buyer_portal(page, buyer_portal_url)
        obs = capture_page_observation(page)

    assert obs.url.endswith("/orders")
    po_links = [e for e in obs.interactive_elements if e.test_id and e.test_id.startswith("po-link-")]
    assert len(po_links) >= 3
    assert any(e.test_id == "po-link-PO-1042" for e in po_links)

    orders_table = next((t for t in obs.tables if t.id == "orders-table"), None)
    assert orders_table is not None
    assert any(h.lower() == "po number" for h in orders_table.headers)
    assert orders_table.row_count == 3


@pytest.mark.browser
@pytest.mark.portal
def test_observation_po_detail_page(buyer_portal_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        login_to_buyer_portal(page, buyer_portal_url)
        page.locator("[data-testid='po-link-PO-1042']").click()
        page.wait_for_url("**/orders/PO-1042")
        obs = capture_page_observation(page)

    assert "PO-1042" in obs.url
    assert "Sweet-Disk" in obs.visible_text
    assert "Crunch-Bar" in obs.visible_text

    lines_table = next((t for t in obs.tables if t.id == "po-lines-table"), None)
    assert lines_table is not None
    assert any(h.lower() == "description" for h in lines_table.headers)
    assert lines_table.row_count == 3


@pytest.mark.browser
@pytest.mark.portal
def test_observation_serializes_to_json(buyer_portal_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        login_to_buyer_portal(page, buyer_portal_url)
        obs = capture_page_observation(page)

    payload = obs.model_dump()
    roundtrip = PageObservation.model_validate(payload)
    assert roundtrip == obs
