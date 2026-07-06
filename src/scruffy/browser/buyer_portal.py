from __future__ import annotations

from datetime import date
from typing import Optional

from playwright.sync_api import Page

from scruffy.models.po import RawPOLine, RawPurchaseOrder


def _parse_date(value: str) -> Optional[date]:
    value = value.strip()
    if not value:
        return None
    return date.fromisoformat(value)


def _parse_float(value: str) -> float:
    return float(value.replace(",", "").strip())


def extract_po_detail(page: Page) -> RawPurchaseOrder:
    """Extract a purchase order from the buyer portal detail page."""
    po_number = page.locator("[data-testid='po-number']").inner_text().strip()
    buyer_name = page.locator("[data-testid='po-buyer']").inner_text().strip()
    order_date = _parse_date(page.locator("[data-testid='po-order-date']").inner_text())

    lines: list[RawPOLine] = []
    rows = page.locator("[data-testid='po-lines-table'] tbody tr")
    for i in range(rows.count()):
        row = rows.nth(i)
        lines.append(
            RawPOLine(
                raw_description=row.locator("[data-testid='line-description']").inner_text().strip(),
                raw_sku=row.locator("[data-testid='line-item-code']").inner_text().strip(),
                quantity=_parse_float(row.locator("[data-testid='line-quantity']").inner_text()),
                unit=row.locator("[data-testid='line-uom']").inner_text().strip(),
            )
        )

    return RawPurchaseOrder(
        buyer_name=buyer_name,
        po_number=po_number,
        order_date=order_date,
        lines=lines,
    )
