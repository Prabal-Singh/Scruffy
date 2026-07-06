from __future__ import annotations

import json
from pathlib import Path

import pytest

from scruffy.llm.actions import BrowserAction
from scruffy.llm.client import OllamaClient, OllamaError
from scruffy.llm.config import OllamaConfig
from scruffy.llm.prompts import action_selection_prompt
from scruffy.models.observation import PageObservation

ROOT = Path(__file__).resolve().parents[1]
ORDERS_FIXTURE = ROOT / "tests" / "fixtures" / "observation_orders_page.json"


def _ollama_available() -> bool:
    try:
        client = OllamaClient(OllamaConfig.from_env())
        client.list_models()
        return True
    except OllamaError:
        return False


pytestmark = pytest.mark.skipif(not _ollama_available(), reason="Ollama not reachable")


@pytest.mark.ollama
def test_ollama_lists_models() -> None:
    client = OllamaClient(OllamaConfig.from_env())
    models = client.list_models()
    assert models
    names = {m["name"] for m in models}
    assert OllamaConfig.from_env().model in names


@pytest.mark.ollama
def test_ollama_structured_action_on_orders_fixture() -> None:
    with ORDERS_FIXTURE.open(encoding="utf-8") as f:
        observation = PageObservation.model_validate(json.load(f))

    client = OllamaClient(OllamaConfig.from_env())
    messages = action_selection_prompt(
        observation.model_dump(),
        goal="Open purchase order PO-1042",
    )
    action = client.chat_structured(messages, BrowserAction)

    assert action.action in {"click", "type", "extract_table", "finish", "fail"}
    assert action.reason
    if action.target_id:
        valid_ids = {e.id for e in observation.interactive_elements}
        assert action.target_id in valid_ids
