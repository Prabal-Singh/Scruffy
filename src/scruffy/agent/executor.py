from __future__ import annotations

from typing import Optional

from playwright.sync_api import Locator, Page

from scruffy.agent.loop_guard import po_from_test_id
from scruffy.browser.buyer_portal import extract_po_detail
from scruffy.llm.actions import BrowserAction
from scruffy.models.observation import PageObservation
from scruffy.models.po import RawPurchaseOrder


class ActionExecutionError(RuntimeError):
    pass


class WrongPoClickError(ActionExecutionError):
    pass


def resolve_locator(page: Page, observation: PageObservation, target_id: str) -> Locator:
    element = observation.element_by_id(target_id)
    if element is None:
        raise ActionExecutionError(f"Unknown target_id {target_id!r}")

    if element.test_id:
        locator = page.locator(f"[data-testid='{element.test_id}']")
        if locator.count() > 0:
            return locator.first

    if element.name:
        locator = page.locator(f"[name='{element.name}']")
        if locator.count() > 0:
            return locator.first

    if element.role == "link" and element.text:
        locator = page.get_by_role("link", name=element.text, exact=True)
        if locator.count() > 0:
            return locator.first

    if element.role == "button" and element.text:
        locator = page.get_by_role("button", name=element.text, exact=True)
        if locator.count() > 0:
            return locator.first

    raise ActionExecutionError(
        f"Could not resolve target_id {target_id!r} (test_id={element.test_id!r}, text={element.text!r})"
    )


def execute_action(
    page: Page,
    observation: PageObservation,
    action: BrowserAction,
    *,
    target_order_id: Optional[str] = None,
) -> str:
    """Execute one constrained browser action. Returns a short status message."""
    if action.action == "click":
        if not action.target_id:
            raise ActionExecutionError("click requires target_id")
        element = observation.element_by_id(action.target_id)
        if element is None:
            raise ActionExecutionError(f"Unknown target_id {action.target_id!r}")
        if element.enabled is False:
            raise ActionExecutionError(
                f"{action.target_id} is disabled; use orders-next when the target order is not visible"
            )
        clicked_order_id = po_from_test_id(element.test_id)
        if target_order_id and clicked_order_id and clicked_order_id != target_order_id:
            raise WrongPoClickError(
                f"Target order is {target_order_id!r}, not {clicked_order_id!r}. "
                "Use orders-next if the target is not in visible_po_numbers."
            )
        locator = resolve_locator(page, observation, action.target_id)
        locator.click()
        page.wait_for_load_state("domcontentloaded")
        suffix = f" ({element.test_id})" if element.test_id else ""
        return f"Clicked {action.target_id}{suffix}"

    if action.action == "type":
        if not action.target_id or action.text is None:
            raise ActionExecutionError("type requires target_id and text")
        locator = resolve_locator(page, observation, action.target_id)
        locator.fill(action.text)
        return f"Typed into {action.target_id}"

    if action.action == "extract_table":
        if "/orders/" in page.url and "po-lines-table" in {t.id for t in observation.tables}:
            return "PO line table visible on detail page"
        raise ActionExecutionError("extract_table requires a PO detail page with a line table")

    if action.action == "finish":
        if "/orders/" in page.url:
            po = extract_po_detail(page)
            return f"Extracted PO {po.po_number} with {len(po.lines)} lines"
        raise ActionExecutionError("finish requires a PO detail page URL")

    if action.action == "fail":
        raise ActionExecutionError(action.reason or "Agent reported failure")

    raise ActionExecutionError(f"Unsupported action: {action.action}")


def extract_po_if_on_detail_page(page: Page) -> RawPurchaseOrder:
    if "/orders/" not in page.url:
        raise ActionExecutionError("Not on a PO detail page")
    return extract_po_detail(page)
