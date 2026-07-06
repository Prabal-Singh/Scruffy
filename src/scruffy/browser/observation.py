from __future__ import annotations

from typing import Any, List

from playwright.sync_api import Page

from scruffy.models.observation import InteractiveElement, PageObservation, TableSummary

_INTERACTIVE_JS = """
() => {
  const selector = [
    "a[href]",
    "button",
    "input:not([type='hidden'])",
    "select",
    "textarea",
    "[role='button']",
    "[role='link']",
  ].join(", ");

  const seen = new Set();
  const elements = [];
  let counter = 1;

  for (const el of document.querySelectorAll(selector)) {
    if (seen.has(el)) continue;
    seen.add(el);

    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") continue;

    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;

    const tag = el.tagName.toLowerCase();
    let role = tag;
    if (tag === "a") role = "link";
    if (tag === "input") role = el.type || "textbox";
    if (el.getAttribute("role")) role = el.getAttribute("role");

    const text = (
      el.innerText ||
      el.value ||
      el.getAttribute("aria-label") ||
      el.getAttribute("placeholder") ||
      el.getAttribute("name") ||
      ""
    ).trim().replace(/\\s+/g, " ");

    elements.push({
      id: `e${counter++}`,
      role,
      text: text.slice(0, 160),
      test_id: el.getAttribute("data-testid"),
      name: el.getAttribute("name"),
      input_type: tag === "input" ? (el.type || "text") : null,
    });
  }

  return elements;
}
"""


def _summarize_tables(page: Page) -> List[TableSummary]:
    summaries: List[TableSummary] = []
    tables = page.locator("table.data-table, table")
    for i in range(tables.count()):
        table = tables.nth(i)
        test_id = table.get_attribute("data-testid") or f"table_{i + 1}"
        headers = [h.strip() for h in table.locator("thead th").all_inner_texts()]
        if not headers:
            headers = [h.strip() for h in table.locator("tr").first.locator("th").all_inner_texts()]
        row_count = table.locator("tbody tr").count()
        if row_count == 0:
            row_count = max(table.locator("tr").count() - 1, 0)
        summaries.append(TableSummary(id=test_id, headers=headers, row_count=row_count))
    return summaries


def _normalize_visible_text(text: str, max_length: int) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_length:
        return collapsed
    return collapsed[: max_length - 3] + "..."


def capture_page_observation(page: Page, *, max_text_length: int = 4000) -> PageObservation:
    """Build a compact observation snapshot from the current page."""
    raw_elements: list[dict[str, Any]] = page.evaluate(_INTERACTIVE_JS)
    interactive_elements = [InteractiveElement.model_validate(item) for item in raw_elements]

    visible_text = _normalize_visible_text(page.locator("body").inner_text(), max_text_length)

    return PageObservation(
        url=page.url,
        title=page.title(),
        visible_text=visible_text,
        interactive_elements=interactive_elements,
        tables=_summarize_tables(page),
    )
