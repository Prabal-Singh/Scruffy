from __future__ import annotations

import json
from typing import Any, List, Optional

from scruffy.agent.models import AgentStep


def _format_history(history: List[AgentStep]) -> str:
    if not history:
        return "(no prior steps)"
    lines = []
    for step in history:
        action = step.action
        status = "ok" if step.success else "failed"
        lines.append(
            f"- step {step.step_number}: {action.action} "
            f"target={action.target_id!r} [{status}] {step.message or action.reason}"
        )
    return "\n".join(lines)


def action_selection_prompt(
    observation: dict[str, Any],
    goal: str,
    history: Optional[List[AgentStep]] = None,
    *,
    target_order_id: Optional[str] = None,
) -> list[dict[str, str]]:
    """Build messages asking the model to pick one constrained browser action."""
    allowed_actions = ["click", "type", "extract_table", "finish", "fail"]
    schema = {
        "action": "one of: " + ", ".join(allowed_actions),
        "target_id": "element id from interactive_elements, or null",
        "text": "string when action is type, else null",
        "reason": "short explanation",
    }

    pagination = observation.get("pagination")
    visible_orders = observation.get("visible_po_numbers") or []

    system = (
        "You are Scruffy, a B2B browser agent. "
        "Choose exactly one next action from the allowed action types. "
        "Only reference target_id values that exist in the current interactive_elements. "
        "Never reuse a target_id from prior steps; ids are reassigned every observation. "
        "On login: type email, type password, then click Sign in once both fields are filled. "
        "On the orders list: click only the order link that matches the target order id. "
        "If visible_po_numbers does not include the target and pagination.has_next is true, "
        "click orders-next instead of opening a different order. "
        "Do not click disabled elements (enabled=false). "
        "On the correct order detail page with line items visible, use finish. "
        "Use fail only if the goal cannot be achieved. "
        "Avoid repeating an action that already failed or did not help. "
        "Respond with JSON matching the schema."
    )

    goal_hints = []
    if target_order_id:
        goal_hints.append(f"Target order id: {target_order_id}")
    if visible_orders:
        goal_hints.append(f"Order ids visible on this page: {', '.join(visible_orders)}")
    if pagination:
        goal_hints.append(
            "Pagination: "
            f"{pagination.get('label')} "
            f"(has_next={pagination.get('has_next')}, has_prev={pagination.get('has_prev')})"
        )
    hints_block = "\n".join(goal_hints) if goal_hints else "(none)"

    user = (
        f"Goal: {goal}\n\n"
        f"Navigation hints:\n{hints_block}\n\n"
        f"Prior steps:\n{_format_history(history or [])}\n\n"
        f"Allowed actions: {', '.join(allowed_actions)}\n\n"
        f"Response JSON schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Page observation:\n{json.dumps(observation, indent=2)}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
