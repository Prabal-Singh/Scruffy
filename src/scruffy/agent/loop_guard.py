from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urlparse

from scruffy.agent.models import AgentStep

_PO_LINK_TEST_ID_RE = re.compile(r"\(po-link-([^)]+)\)")


def po_from_test_id(test_id: Optional[str]) -> Optional[str]:
    if not test_id or not test_id.startswith("po-link-"):
        return None
    return test_id.removeprefix("po-link-")


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def detect_loop(steps: List[AgentStep], *, target_order_id: Optional[str] = None) -> Optional[str]:
    """Return a failure reason when the agent is stuck, else None."""
    if target_order_id and _count_wrong_order_clicks(steps, target_order_id) >= 2:
        return (
            f"Repeated clicks on the wrong order; target is {target_order_id!r}. "
            "Use orders-next when the target is not in visible_po_numbers."
        )

    if len(steps) < 3:
        return None

    if reason := _detect_repeated_signature(steps):
        return reason

    if reason := _detect_url_oscillation(steps):
        return reason

    return None


def _detect_repeated_signature(steps: List[AgentStep]) -> Optional[str]:
    recent = steps[-3:]
    if len(recent) < 3:
        return None

    signatures = [
        (step.action.action, step.action.target_id, step.action.text)
        for step in recent
    ]
    if len(set(signatures)) == 1 and signatures[0][0] in {"click", "type"}:
        action, target_id, _text = signatures[0]
        return f"Repeated identical action {action} target={target_id!r} three times"
    return None


def _detect_url_oscillation(steps: List[AgentStep]) -> Optional[str]:
    recent = [normalize_url(step.url) for step in steps[-4:]]
    if len(recent) < 4:
        return None

    if recent[-4] == recent[-2] and recent[-3] == recent[-1] and recent[-4] != recent[-3]:
        return f"Oscillating between {recent[-4]} and {recent[-3]} without progress"
    return None


def _count_wrong_order_clicks(steps: List[AgentStep], target_order_id: str) -> int:
    count = 0
    for step in steps:
        if step.action.action != "click" or not step.success:
            continue
        order_id = _order_id_from_step(step)
        if order_id and order_id != target_order_id:
            count += 1
    return count


def _order_id_from_step(step: AgentStep) -> Optional[str]:
    if step.message:
        match = _PO_LINK_TEST_ID_RE.search(step.message)
        if match:
            return match.group(1)
    return None
