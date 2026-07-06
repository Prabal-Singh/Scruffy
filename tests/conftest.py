from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "browser: tests that launch a real browser (need network)")
    config.addinivalue_line("markers", "portal: tests that need the fake buyer portal server")
    config.addinivalue_line("markers", "ollama: tests that need the Linux Ollama inference server")
    config.addinivalue_line("markers", "slow: tests that call a real LLM agent loop")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    raise RuntimeError(f"Portal server did not start at {url}")


@pytest.fixture(scope="module")
def buyer_portal_url() -> str:
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "portals" / "v1" / "server.py"), "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(ROOT),
    )
    try:
        _wait_for_server(f"{base}/login")
        yield base
    finally:
        proc.terminate()
        proc.wait(timeout=5)


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
