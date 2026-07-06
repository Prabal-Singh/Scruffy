from __future__ import annotations

from typing import Optional

from scruffy.agent.loop_guard import detect_loop, normalize_url
from scruffy.agent.models import AgentStep
from scruffy.llm.actions import BrowserAction


def _step(
    step_number: int,
    url: str,
    action: str,
    *,
    target_id: Optional[str] = None,
    success: bool = True,
    message: Optional[str] = None,
    reason: str = "",
) -> AgentStep:
    return AgentStep(
        step_number=step_number,
        url=url,
        action=BrowserAction(action=action, target_id=target_id, text=None, reason=reason),
        success=success,
        message=message,
    )


def test_detect_repeated_signature() -> None:
    steps = [
        _step(1, "http://x/orders", "click", target_id="e9", message="Clicked e9 (orders-next)"),
        _step(2, "http://x/orders", "click", target_id="e9", message="Clicked e9 (orders-next)"),
        _step(3, "http://x/orders", "click", target_id="e9", message="Clicked e9 (orders-next)"),
    ]
    reason = detect_loop(steps, target_order_id="PO-1042")
    assert reason is not None
    assert "Repeated identical action" in reason


def test_detect_url_oscillation() -> None:
    steps = [
        _step(1, "http://x/orders", "click", target_id="e5"),
        _step(2, "http://x/orders/PO-1044", "click", target_id="e4"),
        _step(3, "http://x/orders", "click", target_id="e5"),
        _step(4, "http://x/orders/PO-1044", "click", target_id="e4"),
    ]
    reason = detect_loop(steps, target_order_id="PO-1042")
    assert reason is not None
    assert "Oscillating" in reason


def test_detect_wrong_order_clicks() -> None:
    steps = [
        _step(
            1,
            "http://x/orders",
            "click",
            target_id="e5",
            message="Clicked e5 (po-link-PO-1044)",
            reason="open po",
        ),
        _step(
            2,
            "http://x/orders",
            "click",
            target_id="e5",
            message="Clicked e5 (po-link-PO-1044)",
            reason="open po",
        ),
    ]
    reason = detect_loop(steps, target_order_id="PO-1042")
    assert reason is not None
    assert "wrong order" in reason.lower()


def test_detect_wrong_order_clicks_supports_arbitrary_ids() -> None:
    steps = [
        _step(
            1,
            "http://x/orders",
            "click",
            message="Clicked e5 (po-link-ORD-2026-999)",
        ),
        _step(
            2,
            "http://x/orders",
            "click",
            message="Clicked e5 (po-link-ORD-2026-999)",
        ),
    ]
    reason = detect_loop(steps, target_order_id="ORD-2026-001")
    assert reason is not None


def test_wrong_order_guard_disabled_without_target() -> None:
    steps = [
        _step(1, "http://x/orders", "click", message="Clicked e5 (po-link-PO-1044)"),
        _step(2, "http://x/orders", "click", message="Clicked e5 (po-link-PO-1044)"),
    ]
    assert detect_loop(steps, target_order_id=None) is None


def test_normalize_url_strips_query() -> None:
    assert normalize_url("http://127.0.0.1:8002/orders?page=2") == "http://127.0.0.1:8002/orders"
