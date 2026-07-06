from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BrowserConfig:
    """Playwright browser launch settings."""

    headless: bool = True
    slow_mo: int = 0
    screenshot_dir: Path | None = None
    trace_dir: Path | None = None
    timeout_ms: int = 30_000
    viewport: dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
