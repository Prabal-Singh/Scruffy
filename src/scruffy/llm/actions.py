from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class BrowserAction(BaseModel):
    """Constrained browser action the agent may choose (Phase 2 preview)."""

    action: Literal["click", "type", "extract_table", "finish", "fail"]
    target_id: Optional[str] = Field(
        default=None,
        description="Element id from observation.interactive_elements (e.g. e4)",
    )
    text: Optional[str] = Field(
        default=None,
        description="Text to type when action is type",
    )
    reason: str = Field(description="Brief explanation for audit trail")
