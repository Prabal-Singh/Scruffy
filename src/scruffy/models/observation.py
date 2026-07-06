from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class InteractiveElement(BaseModel):
    """A single interactive control visible on the page."""

    id: str
    role: str
    text: str
    test_id: Optional[str] = None
    name: Optional[str] = None
    input_type: Optional[str] = None
    enabled: bool = True


class PaginationState(BaseModel):
    """Pagination metadata when the orders list spans multiple pages."""

    page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    label: str


class TableSummary(BaseModel):
    """Compact summary of an HTML table — headers and row count, not full cell data."""

    id: str
    headers: List[str] = Field(default_factory=list)
    row_count: int = 0


class PageObservation(BaseModel):
    """Compact snapshot of what the browser agent sees on a page."""

    url: str
    title: str
    visible_text: str
    interactive_elements: List[InteractiveElement] = Field(default_factory=list)
    tables: List[TableSummary] = Field(default_factory=list)
    visible_po_numbers: List[str] = Field(default_factory=list)
    pagination: Optional[PaginationState] = None

    def element_by_id(self, element_id: str) -> Optional[InteractiveElement]:
        for element in self.interactive_elements:
            if element.id == element_id:
                return element
        return None

    def elements_by_test_id(self, test_id: str) -> List[InteractiveElement]:
        return [e for e in self.interactive_elements if e.test_id == test_id]
