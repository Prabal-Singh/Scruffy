from __future__ import annotations

import json
from typing import Any


def action_selection_prompt(observation: dict[str, Any], goal: str) -> list[dict[str, str]]:
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
        "Respond with JSON matching the schema."
    )
    user = (
        f"Goal: {goal}\n\n"
        f"Allowed actions: {', '.join(allowed_actions)}\n\n"
        f"Response JSON schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Page observation:\n{json.dumps(observation, indent=2)}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
