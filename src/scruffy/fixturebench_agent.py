"""FixtureBench adapter for Scruffy — deterministic portal agent for CI dogfood.

Implements FixtureBench's BrowserAgent protocol using Scruffy's PO extractors.
No LLM required (safe for GitHub Actions). For agentic evals, use
``ScruffyAgenticAdapter`` when Ollama is available.
"""

from __future__ import annotations

import time
from typing import Optional

from playwright.sync_api import sync_playwright

from scruffy.browser.buyer_portal import (
    BuyerPortalNavigationError,
    extract_po_detail,
    open_po_from_orders,
)


class ScruffyDeterministicAgent:
    """Deterministic Scruffy agent for FixtureBench smoke / baseline cases."""

    @property
    def name(self) -> str:
        return "scruffy-deterministic"

    def run(self, task):
        # Late import so Scruffy unit tests don't require fixturebench installed.
        from fixturebench.adapters.protocol import AgentRunResult
        from fixturebench.models.po import RawPurchaseOrder as FBPO

        started = time.perf_counter()
        steps = 0

        if not task.target_id:
            return self._run_empty(task, started)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=task.headless)
                page = browser.new_page()
                page.goto(f"{task.url}/login", wait_until="domcontentloaded")
                steps += 1

                page.fill('[data-testid="login-email"], input[name="email"]', task.email)
                page.fill(
                    '[data-testid="login-password"], input[name="password"]',
                    task.password,
                )
                page.click('[data-testid="login-submit"], button[type="submit"]')
                page.wait_for_load_state("domcontentloaded")
                steps += 1

                # MFA (FixtureBench v20)
                if page.locator('[data-testid="mfa-code"]').count():
                    page.fill('[data-testid="mfa-code"]', "424242")
                    page.click('[data-testid="mfa-submit"]')
                    page.wait_for_load_state("domcontentloaded")
                    steps += 1

                # Anti-bot interstitial (v18)
                if page.locator('[data-testid="verify-checkbox"]').count():
                    page.check('[data-testid="verify-checkbox"]')
                    page.click('[data-testid="verify-submit"]')
                    page.wait_for_load_state("domcontentloaded")
                    steps += 1

                self._reveal_target(page, task.target_id)
                steps += 1

                self._open_target(page, task.target_id)
                steps += 1

                expand = page.locator('[data-testid="expand-line-items"]')
                if expand.count():
                    expand.first.click()
                    page.wait_for_timeout(200)
                    steps += 1

                ack = page.locator('[data-testid="acknowledge-button"]')
                if ack.count():
                    ack.first.click()
                    page.wait_for_load_state("domcontentloaded")
                    steps += 1

                refresh = page.locator('[data-testid="refresh-from-source"]')
                if refresh.count():
                    refresh.first.click()
                    page.wait_for_load_state("domcontentloaded")
                    steps += 1

                page.wait_for_timeout(1600)

                try:
                    scruffy_po = extract_po_detail(page)
                except Exception:
                    # Messy-DOM / iframe / unlabeled — best-effort fallback
                    scruffy_po = self._extract_fallback(page, task.target_id)

                browser.close()

                if scruffy_po is None or not scruffy_po.lines:
                    return AgentRunResult(
                        success=False,
                        failure_reason="Could not extract PO line items",
                        step_count=steps,
                        total_duration_ms=(time.perf_counter() - started) * 1000,
                        metadata={"agent": self.name},
                    )

                fb_po = FBPO.model_validate(scruffy_po.model_dump(mode="json"))
                return AgentRunResult(
                    success=True,
                    payload=fb_po,
                    step_count=steps,
                    total_duration_ms=(time.perf_counter() - started) * 1000,
                    metadata={"agent": self.name, "source": "scruffy.browser.buyer_portal"},
                )
        except Exception as exc:  # noqa: BLE001
            return AgentRunResult(
                success=False,
                failure_reason=str(exc),
                step_count=steps,
                total_duration_ms=(time.perf_counter() - started) * 1000,
                metadata={"agent": self.name},
            )

    def _run_empty(self, task, started: float):
        from fixturebench.adapters.protocol import AgentRunResult

        steps = 0
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=task.headless)
                page = browser.new_page()
                page.goto(f"{task.url}/login", wait_until="domcontentloaded")
                steps += 1
                page.fill('[data-testid="login-email"], input[name="email"]', task.email)
                page.fill(
                    '[data-testid="login-password"], input[name="password"]',
                    task.password,
                )
                page.click('[data-testid="login-submit"], button[type="submit"]')
                page.wait_for_load_state("domcontentloaded")
                steps += 1
                empty = page.locator('[data-testid="empty-state"]')
                ok = empty.count() > 0
                browser.close()
                return AgentRunResult(
                    success=ok,
                    payload=None,
                    failure_reason=None if ok else "Empty state not found",
                    step_count=steps,
                    total_duration_ms=(time.perf_counter() - started) * 1000,
                    metadata={"agent": self.name},
                )
        except Exception as exc:  # noqa: BLE001
            return AgentRunResult(
                success=False,
                failure_reason=str(exc),
                step_count=steps,
                total_duration_ms=(time.perf_counter() - started) * 1000,
                metadata={"agent": self.name},
            )

    def _reveal_target(self, page, target_id: str) -> None:
        if page.locator('[data-testid="tab-all"]').count():
            if page.locator(f'[data-testid="po-link-{target_id}"]').count() == 0:
                page.click('[data-testid="tab-all"]')
                page.wait_for_load_state("domcontentloaded")

        if page.locator('[data-testid="search-input"]').count():
            if page.locator(f'[data-testid="po-link-{target_id}"]').count() == 0:
                page.fill('[data-testid="search-input"]', target_id)
                page.click('[data-testid="search-submit"]')
                page.wait_for_load_state("domcontentloaded")

        viewport = page.locator('[data-testid="virtual-viewport"]')
        if viewport.count():
            for _ in range(30):
                if page.locator(f'[data-testid="po-link-{target_id}"]').count():
                    return
                viewport.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")
                page.wait_for_timeout(60)

    def _open_target(self, page, target_id: str) -> None:
        midwest = page.locator(
            f'a[data-testid="po-link-{target_id}"][data-buyer="Midwest Foods Co-op"]'
        )
        if midwest.count():
            midwest.first.click()
            page.wait_for_load_state("domcontentloaded")
            return

        try:
            open_po_from_orders(page, target_id)
            return
        except BuyerPortalNavigationError:
            pass

        link = page.locator(
            f'[data-testid="po-link-{target_id}"], a:has-text("{target_id}")'
        ).first
        link.click()
        page.wait_for_load_state("domcontentloaded")

    def _extract_fallback(self, page, target_id: str):
        from scruffy.models.po import RawPOLine, RawPurchaseOrder

        buyer_el = page.locator('[data-testid="po-buyer"]')
        date_el = page.locator('[data-testid="po-order-date"]')
        buyer = buyer_el.first.inner_text().strip() if buyer_el.count() else None
        order_date = None
        if date_el.count():
            raw = date_el.first.inner_text().strip()
            try:
                from datetime import date

                order_date = date.fromisoformat(raw)
            except ValueError:
                order_date = None

        lines = []
        rows = page.locator('[data-testid="po-lines-table"] tbody tr')
        for i in range(rows.count()):
            row = rows.nth(i)
            lines.append(
                RawPOLine(
                    raw_description=row.locator('[data-testid="line-description"]').inner_text().strip(),
                    raw_sku=row.locator('[data-testid="line-item-code"]').inner_text().strip(),
                    quantity=float(row.locator('[data-testid="line-quantity"]').inner_text().strip()),
                    unit=row.locator('[data-testid="line-uom"]').inner_text().strip(),
                )
            )
        if not lines:
            return None
        return RawPurchaseOrder(
            buyer_name=buyer,
            po_number=target_id,
            order_date=order_date,
            lines=lines,
        )


class ScruffyAgenticAdapter:
    """Wraps Scruffy's LLM agent loop for FixtureBench (requires Ollama)."""

    @property
    def name(self) -> str:
        return "scruffy-agentic"

    def run(self, task):
        from fixturebench.adapters.protocol import AgentRunResult
        from fixturebench.models.po import RawPurchaseOrder as FBPO
        from scruffy.agent.loop import run_agent
        from scruffy.llm.client import OllamaError

        try:
            result = run_agent(
                task.url,
                task.goal,
                target_order_id=task.target_id or None,
                max_steps=task.max_steps,
                headless=task.headless,
                screenshot_dir=task.screenshot_dir,
                trace_dir=task.trace_dir,
            )
        except OllamaError as exc:
            return AgentRunResult(
                success=False,
                failure_reason=f"Ollama unavailable: {exc}",
                metadata={"agent": self.name},
            )

        payload = None
        if result.po is not None:
            payload = FBPO.model_validate(result.po.model_dump(mode="json"))

        return AgentRunResult(
            success=result.success,
            payload=payload,
            failure_reason=result.failure_reason,
            step_count=len(result.steps),
            total_duration_ms=result.total_duration_ms,
            llm_duration_ms=sum(
                (s.llm_duration_ms or 0.0) for s in result.steps
            ),
            metadata={"agent": self.name, "goal": result.goal},
        )
