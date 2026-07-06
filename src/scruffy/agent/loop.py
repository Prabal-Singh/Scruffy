from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from scruffy.agent.executor import ActionExecutionError, WrongPoClickError, execute_action, extract_po_if_on_detail_page
from scruffy.agent.loop_guard import detect_loop
from scruffy.agent.models import AgentResult, AgentStep
from scruffy.browser.config import BrowserConfig
from scruffy.browser.observation import capture_page_observation
from scruffy.browser.runner import BrowserRunner
from scruffy.llm.actions import BrowserAction
from scruffy.llm.client import OllamaClient, OllamaError
from scruffy.llm.config import OllamaConfig
from scruffy.llm.prompts import action_selection_prompt
from scruffy.models.po import RawPurchaseOrder


def _choose_action(
    client: OllamaClient,
    observation_json: dict,
    goal: str,
    history: list[AgentStep],
    *,
    target_order_id: Optional[str] = None,
) -> BrowserAction:
    messages = action_selection_prompt(
        observation_json,
        goal,
        history,
        target_order_id=target_order_id,
    )
    return client.chat_structured(messages, BrowserAction)


def run_agent(
    portal_url: str,
    goal: str,
    *,
    target_order_id: Optional[str] = None,
    start_path: str = "/login",
    max_steps: int = 12,
    headless: bool = True,
    ollama_config: Optional[OllamaConfig] = None,
    screenshot_dir: Optional[Path] = None,
    trace_dir: Optional[Path] = None,
) -> AgentResult:
    """Run a constrained ReAct loop: observe → LLM action → Playwright execute."""
    client = OllamaClient(ollama_config)
    runner = BrowserRunner(
        BrowserConfig(
            headless=headless,
            screenshot_dir=screenshot_dir,
            trace_dir=trace_dir,
        )
    )
    steps: list[AgentStep] = []
    base = portal_url.rstrip("/")

    with runner.session() as (_pw, _browser, _context, page):
        page.goto(f"{base}{start_path}")
        return _run_loop(
            page=page,
            client=client,
            goal=goal,
            target_order_id=target_order_id,
            max_steps=max_steps,
            steps=steps,
            runner=runner,
        )


def _run_loop(
    page: Page,
    client: OllamaClient,
    goal: str,
    max_steps: int,
    steps: list[AgentStep],
    runner: BrowserRunner,
    *,
    target_order_id: Optional[str] = None,
) -> AgentResult:
    po: Optional[RawPurchaseOrder] = None
    run_started = time.perf_counter()

    for step_number in range(1, max_steps + 1):
        if loop_reason := detect_loop(steps, target_order_id=target_order_id):
            return _finalize_result(
                goal=goal,
                steps=steps,
                success=False,
                failure_reason=loop_reason,
                run_started=run_started,
            )

        step_started = time.perf_counter()
        observation = capture_page_observation(page)
        runner.screenshot(page, f"agent_step_{step_number:02d}")

        llm_started = time.perf_counter()
        try:
            action = _choose_action(
                client,
                observation.model_dump(),
                goal,
                steps,
                target_order_id=target_order_id,
            )
        except OllamaError as exc:
            return _finalize_result(
                goal=goal,
                steps=steps,
                success=False,
                failure_reason=f"LLM error: {exc}",
                run_started=run_started,
            )

        llm_duration_ms = (time.perf_counter() - llm_started) * 1000

        if action.action == "finish":
            try:
                po = extract_po_if_on_detail_page(page)
                if target_order_id and po.po_number != target_order_id:
                    raise WrongPoClickError(
                        f"On {po.po_number!r} but target is {target_order_id!r}. "
                        "Return to the orders list and paginate to the correct order."
                    )
                steps.append(
                    _make_step(
                        step_number=step_number,
                        page=page,
                        action=action,
                        success=True,
                        message=f"Extracted {po.po_number}",
                        step_started=step_started,
                        llm_duration_ms=llm_duration_ms,
                    )
                )
                return _finalize_result(
                    goal=goal,
                    steps=steps,
                    success=True,
                    po=po,
                    run_started=run_started,
                )
            except WrongPoClickError as exc:
                steps.append(
                    _make_step(
                        step_number=step_number,
                        page=page,
                        action=action,
                        success=False,
                        message=str(exc),
                        step_started=step_started,
                        llm_duration_ms=llm_duration_ms,
                    )
                )
                continue
            except ActionExecutionError as exc:
                steps.append(
                    _make_step(
                        step_number=step_number,
                        page=page,
                        action=action,
                        success=False,
                        message=str(exc),
                        step_started=step_started,
                        llm_duration_ms=llm_duration_ms,
                    )
                )
                return _finalize_result(
                    goal=goal,
                    steps=steps,
                    success=False,
                    failure_reason=str(exc),
                    run_started=run_started,
                )

        if action.action == "fail":
            steps.append(
                _make_step(
                    step_number=step_number,
                    page=page,
                    action=action,
                    success=False,
                    message=action.reason,
                    step_started=step_started,
                    llm_duration_ms=llm_duration_ms,
                )
            )
            return _finalize_result(
                goal=goal,
                steps=steps,
                success=False,
                failure_reason=action.reason,
                run_started=run_started,
            )

        try:
            message = execute_action(
                page, observation, action, target_order_id=target_order_id
            )
            steps.append(
                _make_step(
                    step_number=step_number,
                    page=page,
                    action=action,
                    success=True,
                    message=message,
                    step_started=step_started,
                    llm_duration_ms=llm_duration_ms,
                )
            )
        except WrongPoClickError as exc:
            steps.append(
                _make_step(
                    step_number=step_number,
                    page=page,
                    action=action,
                    success=False,
                    message=str(exc),
                    step_started=step_started,
                    llm_duration_ms=llm_duration_ms,
                )
            )
            continue
        except ActionExecutionError as exc:
            steps.append(
                _make_step(
                    step_number=step_number,
                    page=page,
                    action=action,
                    success=False,
                    message=str(exc),
                    step_started=step_started,
                    llm_duration_ms=llm_duration_ms,
                )
            )
            return _finalize_result(
                goal=goal,
                steps=steps,
                success=False,
                failure_reason=str(exc),
                run_started=run_started,
            )

    return _finalize_result(
        goal=goal,
        steps=steps,
        success=False,
        failure_reason=f"Exceeded max_steps ({max_steps})",
        run_started=run_started,
    )


def _make_step(
    *,
    step_number: int,
    page: Page,
    action: BrowserAction,
    success: bool,
    message: str,
    step_started: float,
    llm_duration_ms: float,
) -> AgentStep:
    return AgentStep(
        step_number=step_number,
        url=page.url,
        action=action,
        success=success,
        message=message,
        duration_ms=(time.perf_counter() - step_started) * 1000,
        llm_duration_ms=llm_duration_ms,
    )


def _finalize_result(
    *,
    goal: str,
    steps: list[AgentStep],
    success: bool,
    run_started: float,
    po: Optional[RawPurchaseOrder] = None,
    failure_reason: Optional[str] = None,
) -> AgentResult:
    return AgentResult(
        goal=goal,
        steps=steps,
        success=success,
        po=po,
        failure_reason=failure_reason,
        total_duration_ms=(time.perf_counter() - run_started) * 1000,
    )
