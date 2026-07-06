from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class RawPOLine(BaseModel):
    """A single line item as seen on a buyer portal (pre-normalization)."""

    raw_description: str
    raw_sku: str | None = None
    quantity: float
    unit: str | None = None


class RawPurchaseOrder(BaseModel):
    """Purchase order extracted from a buyer portal before SKU normalization."""

    buyer_name: str | None = None
    po_number: str
    order_date: date | None = None
    lines: list[RawPOLine] = Field(default_factory=list)


class TableRow(BaseModel):
    """Generic key-value row from an HTML table (used in Phase 1 practice scraping)."""

    cells: dict[str, str]
