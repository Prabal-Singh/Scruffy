import pytest

from scruffy.agent.executor import ActionExecutionError, execute_action, resolve_locator
from scruffy.browser.observation import capture_page_observation
from scruffy.browser.scraper import login_to_buyer_portal
from scruffy.llm.actions import BrowserAction


@pytest.mark.browser
@pytest.mark.portal
def test_executor_clicks_po_link(buyer_portal_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        login_to_buyer_portal(page, buyer_portal_url)
        obs = capture_page_observation(page)
        po_link = next(e for e in obs.interactive_elements if e.test_id == "po-link-PO-1042")

        execute_action(
            page,
            obs,
            BrowserAction(action="click", target_id=po_link.id, reason="open po"),
        )
        page.wait_for_url("**/orders/PO-1042")


@pytest.mark.browser
@pytest.mark.portal
def test_executor_types_login_fields(buyer_portal_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        page.goto(f"{buyer_portal_url}/login")
        obs = capture_page_observation(page)
        email = next(e for e in obs.interactive_elements if e.test_id == "login-email")
        password = next(e for e in obs.interactive_elements if e.test_id == "login-password")

        execute_action(
            page,
            obs,
            BrowserAction(action="type", target_id=email.id, text="vendor@scruffy.test", reason="email"),
        )
        execute_action(
            page,
            obs,
            BrowserAction(action="type", target_id=password.id, text="scruffy123", reason="password"),
        )

        obs2 = capture_page_observation(page)
        submit = next(e for e in obs2.interactive_elements if e.test_id == "login-submit")
        execute_action(page, obs2, BrowserAction(action="click", target_id=submit.id, reason="submit"))
        page.wait_for_url("**/orders")


@pytest.mark.browser
@pytest.mark.portal
def test_resolve_locator_unknown_id_raises(buyer_portal_url: str, browser_runner) -> None:
    with browser_runner.session() as (_pw, _browser, _context, page):
        page.goto(f"{buyer_portal_url}/login")
        obs = capture_page_observation(page)
        with pytest.raises(ActionExecutionError):
            resolve_locator(page, obs, "e999")
