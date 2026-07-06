import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "browser: tests that launch a real browser (need network)")
