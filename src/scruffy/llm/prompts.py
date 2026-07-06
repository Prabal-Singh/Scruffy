from __future__ import annotations

import json
from typing import Any, List

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
    history: List[AgentStep] | None = None,
) -> list[dict[str, str]]:
    """Build messages asking the model to pick one constrained browser action."""
    allowed_actions = ["click", "type", "extract_table", "finish", "fail"]
    schema = {
        "action": "one of: " + ", ".join(allowed_actions),
        "target_id": "element id from interactive_elements, or null",
        "text": "string when action is type, else null",
        "reason": "short explanation",
    }

    system = (
        "You are Scruffy, a B2B browser agent. "
        "Choose exactly one next action from the allowed action types. "
        "Only reference target_id values that exist in interactive_elements. "
        "Use type to fill login email/password fields, then click Sign in. "
        "On the orders list, click the PO link matching the goal. "
        "On a PO detail page with line items, use finish. "
        "Use fail only if the goal cannot be achieved. "
        "Respond with JSON matching the schema."
    )
    user = (
        f"Goal: {goal}\n\n"
        f"Prior steps:\n{_format_history(history or [])}\n\n"
        f"Allowed actions: {', '.join(allowed_actions)}\n\n"
        f"Response JSON schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Page observation:\n{json.dumps(observation, indent=2)}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
