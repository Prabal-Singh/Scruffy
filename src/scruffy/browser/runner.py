from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from scruffy.browser.config import BrowserConfig


class BrowserRunner:
    """Thin Playwright harness for deterministic browser automation."""

    def __init__(self, config: BrowserConfig | None = None) -> None:
        self.config = config or BrowserConfig()

    @contextmanager
    def session(self) -> Generator[tuple[Playwright, Browser, BrowserContext, Page], None, None]:
        """Launch a browser session. Traces and screenshots go to configured dirs."""
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=self.config.headless,
                slow_mo=self.config.slow_mo,
            )
            context = browser.new_context(viewport=self.config.viewport)
            context.set_default_timeout(self.config.timeout_ms)

            if self.config.trace_dir:
                self.config.trace_dir.mkdir(parents=True, exist_ok=True)
                context.tracing.start(screenshots=True, snapshots=True, sources=True)

            page = context.new_page()
            try:
                yield pw, browser, context, page
            finally:
                if self.config.trace_dir:
                    trace_path = self.config.trace_dir / "session.trace.zip"
                    context.tracing.stop(path=str(trace_path))
                context.close()
                browser.close()

    def screenshot(self, page: Page, name: str) -> Path | None:
        if not self.config.screenshot_dir:
            return None
        self.config.screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = self.config.screenshot_dir / f"{name}.png"
        page.screenshot(path=str(path), full_page=True)
        return path
