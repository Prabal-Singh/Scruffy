from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "browser: tests that launch a real browser (need network)")
    config.addinivalue_line("markers", "portal: tests that need the fake buyer portal server")
    config.addinivalue_line("markers", "ollama: tests that need the Linux Ollama inference server")
    config.addinivalue_line("markers", "slow: tests that call a real LLM agent loop")
    config.addinivalue_line("markers", "eval: tests for the eval runner infrastructure")


@pytest.fixture(scope="module")
def buyer_portal_url() -> str:
    from scruffy.eval.portal import ManagedPortal

    with ManagedPortal("v1", ROOT) as base:
        yield base


@pytest.fixture(scope="module")
def buyer_portal_v2_url() -> str:
    from scruffy.eval.portal import ManagedPortal

    with ManagedPortal("v2", ROOT) as base:
        yield base


@pytest.fixture(scope="module")
def buyer_portal_v3_url() -> str:
    from scruffy.eval.portal import ManagedPortal

    with ManagedPortal("v3", ROOT) as base:
        yield base


@pytest.fixture
def browser_runner(tmp_path: Path):
    from scruffy.browser.config import BrowserConfig
    from scruffy.browser.runner import BrowserRunner

    return BrowserRunner(
        BrowserConfig(
            headless=True,
            screenshot_dir=tmp_path / "screenshots",
            trace_dir=tmp_path / "traces",
        )
    )


@pytest.fixture
def expected_po_1042() -> dict:
    fixture_path = ROOT / "tests" / "fixtures" / "expected_po_1042.json"
    with fixture_path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def expected_po_1042_v2() -> dict:
    fixture_path = ROOT / "tests" / "fixtures" / "expected_po_1042_v2.json"
    with fixture_path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def expected_po_1042_v3() -> dict:
    fixture_path = ROOT / "tests" / "fixtures" / "expected_po_1042_v3.json"
    with fixture_path.open(encoding="utf-8") as f:
        return json.load(f)
