#!/usr/bin/env python3
"""Test connectivity and structured JSON output from the Linux Ollama box.

Examples:
    python scripts/test_ollama.py
    python scripts/test_ollama.py --url http://192.168.0.7:11434 --model qwen2.5:14b
    SCRUFFY_OLLAMA_URL=http://192.168.0.7:11434 python scripts/test_ollama.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scruffy.llm.actions import BrowserAction
from scruffy.llm.client import OllamaClient, OllamaError
from scruffy.llm.config import OllamaConfig
from scruffy.llm.prompts import action_selection_prompt
from scruffy.models.observation import PageObservation

ROOT = Path(__file__).resolve().parents[1]
ORDERS_FIXTURE = ROOT / "tests" / "fixtures" / "observation_orders_page.json"


def _load_observation() -> PageObservation:
    with ORDERS_FIXTURE.open(encoding="utf-8") as f:
        return PageObservation.model_validate(json.load(f))


def _validate_action(observation: PageObservation, action: BrowserAction) -> list[str]:
    warnings: list[str] = []
    valid_ids = {element.id for element in observation.interactive_elements}

    if action.action in {"click", "type"} and not action.target_id:
        warnings.append("click/type actions should include target_id")
    if action.target_id and action.target_id not in valid_ids:
        warnings.append(f"target_id {action.target_id!r} not in observation elements")
    if action.action == "type" and not action.text:
        warnings.append("type action should include text")

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Ollama connectivity and JSON action selection")
    parser.add_argument("--url", default=OllamaConfig.base_url, help="Ollama base URL")
    parser.add_argument("--model", default=OllamaConfig.model, help="Ollama model name")
    parser.add_argument(
        "--goal",
        default="Open purchase order PO-1042",
        help="Agent goal for the sample observation test",
    )
    args = parser.parse_args()

    client = OllamaClient(OllamaConfig(base_url=args.url, model=args.model))

    print(f"Checking Ollama at {client.base_url} ...")
    models = client.list_models()
    names = [m.get("name", "?") for m in models]
    print(f"  Models: {', '.join(names) or '(none)'}")
    if args.model not in names:
        print(f"  WARNING: requested model {args.model!r} not in /api/tags")

    print("\nSmoke test (generate) ...")
    reply = client.generate("Reply with exactly: scruffy online", json_mode=False)
    print(f"  Response: {reply!r}")

    print("\nStructured action test (orders page observation) ...")
    observation = _load_observation()
    messages = action_selection_prompt(observation.model_dump(), args.goal)
    action = client.chat_structured(messages, BrowserAction)
    print(json.dumps(action.model_dump(), indent=2))

    warnings = _validate_action(observation, action)
    if action.target_id == "e4" and action.action == "click":
        print("\n  OK: selected click on PO-1042 link (e4)")
    elif warnings:
        print("\n  Warnings:")
        for warning in warnings:
            print(f"    - {warning}")
    else:
        print("\n  Action parsed successfully (review choice manually)")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OllamaError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
