from __future__ import annotations

import pytest

from scruffy.agent.loop import run_agent
from scruffy.browser.scraper import DEFAULT_EMAIL, DEFAULT_PASSWORD
from scruffy.llm.client import OllamaClient, OllamaError
from scruffy.llm.config import OllamaConfig


def _ollama_available() -> bool:
    try:
        OllamaClient(OllamaConfig.from_env()).list_models()
        return True
    except OllamaError:
        return False


pytestmark = [
    pytest.mark.skipif(not _ollama_available(), reason="Ollama not reachable"),
    pytest.mark.ollama,
    pytest.mark.portal,
    pytest.mark.browser,
]


@pytest.mark.slow
def test_agent_extracts_po_1042(buyer_portal_url: str) -> None:
    goal = (
        f"Log into the buyer portal using email {DEFAULT_EMAIL} and password {DEFAULT_PASSWORD}. "
        "Open purchase order PO-1042 and finish when the PO line items are visible."
    )
    result = run_agent(buyer_portal_url, goal, max_steps=12, headless=True)

    assert result.success, result.failure_reason
    assert result.po is not None
    assert result.po.po_number == "PO-1042"
    assert len(result.po.lines) == 3
    assert result.po.lines[0].raw_description == "Sweet-Disk"
    assert len(result.steps) >= 4
