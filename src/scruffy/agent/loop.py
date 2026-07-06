from __future__ import annotations

from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from scruffy.agent.executor import ActionExecutionError, execute_action, extract_po_if_on_detail_page
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
) -> BrowserAction:
    messages = action_selection_prompt(observation_json, goal, history)
    return client.chat_structured(messages, BrowserAction)


def run_agent(
    portal_url: str,
    goal: str,
    *,
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
) -> AgentResult:
    po: Optional[RawPurchaseOrder] = None

    for step_number in range(1, max_steps + 1):
        observation = capture_page_observation(page)
        runner.screenshot(page, f"agent_step_{step_number:02d}")

        try:
            action = _choose_action(
                client,
                observation.model_dump(),
                goal,
                steps,
            )
        except OllamaError as exc:
            return AgentResult(
                goal=goal,
                steps=steps,
                success=False,
                failure_reason=f"LLM error: {exc}",
            )

        if action.action == "finish":
            try:
                po = extract_po_if_on_detail_page(page)
                steps.append(
                    AgentStep(
                        step_number=step_number,
                        url=page.url,
                        action=action,
                        success=True,
                        message=f"Extracted {po.po_number}",
                    )
                )
                return AgentResult(goal=goal, steps=steps, success=True, po=po)
            except ActionExecutionError as exc:
                steps.append(
                    AgentStep(
                        step_number=step_number,
                        url=page.url,
                        action=action,
                        success=False,
                        message=str(exc),
                    )
                )
                return AgentResult(
                    goal=goal,
                    steps=steps,
                    success=False,
                    failure_reason=str(exc),
                )

        if action.action == "fail":
            steps.append(
                AgentStep(
                    step_number=step_number,
                    url=page.url,
                    action=action,
                    success=False,
                    message=action.reason,
                )
            )
            return AgentResult(
                goal=goal,
                steps=steps,
                success=False,
                failure_reason=action.reason,
            )

        try:
            message = execute_action(page, observation, action)
            steps.append(
                AgentStep(
                    step_number=step_number,
                    url=page.url,
                    action=action,
                    success=True,
                    message=message,
                )
            )
        except ActionExecutionError as exc:
            steps.append(
                AgentStep(
                    step_number=step_number,
                    url=page.url,
                    action=action,
                    success=False,
                    message=str(exc),
                )
            )
            return AgentResult(
                goal=goal,
                steps=steps,
                success=False,
                failure_reason=str(exc),
            )

    return AgentResult(
        goal=goal,
        steps=steps,
        success=False,
        failure_reason=f"Exceeded max_steps ({max_steps})",
    )
