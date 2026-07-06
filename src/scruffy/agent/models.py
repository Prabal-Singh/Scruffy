from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from scruffy.llm.actions import BrowserAction
from scruffy.models.po import RawPurchaseOrder


class AgentStep(BaseModel):
    """One observe → act iteration in the agent trace."""

    step_number: int
    url: str
    action: BrowserAction
    success: bool
    message: Optional[str] = None


class AgentResult(BaseModel):
    """Terminal outcome of an agent run."""

    goal: str
    steps: List[AgentStep] = Field(default_factory=list)
    success: bool
    po: Optional[RawPurchaseOrder] = None
    failure_reason: Optional[str] = None
