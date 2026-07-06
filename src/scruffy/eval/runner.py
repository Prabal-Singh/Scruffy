from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from scruffy.agent.loop import run_agent
from scruffy.eval.cases import (
    build_goal,
    case_headless,
    case_max_steps,
    load_expected_po,
    load_suite,
    resolve_cases,
)
from scruffy.eval.models import (
    EvalCase,
    EvalCaseMetrics,
    EvalCaseResult,
    EvalDefaults,
    EvalReport,
    EvalSummary,
    EvalSuite,
)
from scruffy.eval.portal import ManagedPortal
from scruffy.eval.report import new_run_id, utc_now, write_report
from scruffy.eval.scorer import compare_po
from scruffy.llm.config import OllamaConfig


class EvalRunner:
    """Run registered eval cases and produce scored reports."""

    def __init__(
        self,
        root: Path,
        *,
        suite_path: Optional[Path] = None,
        ollama_config: Optional[OllamaConfig] = None,
        output_dir: Optional[Path] = None,
        screenshot_dir: Optional[Path] = None,
        trace_dir: Optional[Path] = None,
    ) -> None:
        self.root = root
        self.suite_path = suite_path or (root / "eval" / "cases.json")
        self.ollama_config = ollama_config or OllamaConfig.from_env()
        self.output_dir = output_dir or (root / "eval-results")
        self.screenshot_dir = screenshot_dir or (root / "eval-results" / "screenshots")
        self.trace_dir = trace_dir or (root / "eval-results" / "traces")

    def load_suite(self) -> EvalSuite:
        return load_suite(self.suite_path)

    def run(
        self,
        *,
        case_ids: Optional[Iterable[str]] = None,
        tags: Optional[Iterable[str]] = None,
        headless: Optional[bool] = None,
        write_results: bool = True,
    ) -> EvalReport:
        suite = self.load_suite()
        cases = resolve_cases(suite, case_ids=case_ids, tags=tags)
        if not cases:
            raise ValueError("No eval cases matched the requested filters")

        started_at = utc_now()
        case_results: list[EvalCaseResult] = []

        for case in cases:
            case_results.append(self._run_case(case, suite.defaults, headless=headless))

        finished_at = utc_now()
        report = EvalReport(
            run_id=new_run_id(started_at),
            started_at=started_at,
            finished_at=finished_at,
            ollama_url=self.ollama_config.base_url,
            ollama_model=self.ollama_config.model,
            cases=case_results,
            summary=_build_summary(case_results),
        )

        if write_results:
            write_report(report, self.output_dir)

        return report

    def _run_case(
        self,
        case: EvalCase,
        defaults: EvalDefaults,
        *,
        headless: Optional[bool],
    ) -> EvalCaseResult:
        expected = load_expected_po(self.root, case)
        goal = build_goal(case, defaults)
        resolved_headless = headless if headless is not None else case_headless(case, defaults)
        max_steps = case_max_steps(case, defaults)

        if case.manage_portal and case.portal_url is None:
            with ManagedPortal(case.portal, self.root) as portal_url:
                agent_result = run_agent(
                    portal_url,
                    goal,
                    target_order_id=case.po_number,
                    max_steps=max_steps,
                    headless=resolved_headless,
                    ollama_config=self.ollama_config,
                    screenshot_dir=self.screenshot_dir / case.id,
                    trace_dir=self.trace_dir / case.id,
                )
                return self._score_case(case, portal_url, expected, agent_result)

        portal_url = case.portal_url or _default_portal_url(case.portal)
        agent_result = run_agent(
            portal_url,
            goal,
            target_order_id=case.po_number,
            max_steps=max_steps,
            headless=resolved_headless,
            ollama_config=self.ollama_config,
            screenshot_dir=self.screenshot_dir / case.id,
            trace_dir=self.trace_dir / case.id,
        )
        return self._score_case(case, portal_url, expected, agent_result)

    def _score_case(
        self,
        case: EvalCase,
        portal_url: str,
        expected,
        agent_result,
    ) -> EvalCaseResult:
        comparison = None
        extraction_pass = False

        if agent_result.po is not None:
            comparison = compare_po(agent_result.po, expected)
            extraction_pass = comparison.passed

        metrics = _case_metrics(agent_result)
        passed = agent_result.success and extraction_pass

        return EvalCaseResult(
            case_id=case.id,
            portal=case.portal,
            portal_url=portal_url,
            po_number=case.po_number,
            agent_success=agent_result.success,
            extraction_pass=extraction_pass,
            passed=passed,
            metrics=metrics,
            failure_reason=agent_result.failure_reason,
            po_comparison=comparison,
            agent_result=agent_result,
        )


def _default_portal_url(portal: str) -> str:
    from scruffy.eval.portal import PORTAL_SPECS

    default_port = PORTAL_SPECS[portal]["default_port"]
    return f"http://127.0.0.1:{default_port}"


def _case_metrics(agent_result) -> EvalCaseMetrics:
    step_count = len(agent_result.steps)
    total_duration_ms = agent_result.total_duration_ms or 0.0
    llm_duration_ms = sum(step.llm_duration_ms or 0.0 for step in agent_result.steps)
    avg_step_duration_ms = total_duration_ms / step_count if step_count else 0.0
    avg_llm_duration_ms = llm_duration_ms / step_count if step_count else 0.0

    return EvalCaseMetrics(
        step_count=step_count,
        total_duration_ms=total_duration_ms,
        llm_duration_ms=llm_duration_ms,
        avg_step_duration_ms=avg_step_duration_ms,
        avg_llm_duration_ms=avg_llm_duration_ms,
    )


def _build_summary(case_results: list[EvalCaseResult]) -> EvalSummary:
    total = len(case_results)
    passed = sum(1 for result in case_results if result.passed)
    agent_successes = sum(1 for result in case_results if result.agent_success)
    extraction_passes = sum(1 for result in case_results if result.extraction_pass)

    return EvalSummary(
        total=total,
        passed=passed,
        failed=total - passed,
        agent_success_rate=agent_successes / total if total else 0.0,
        extraction_accuracy=extraction_passes / total if total else 0.0,
        pass_rate=passed / total if total else 0.0,
        avg_steps=sum(result.metrics.step_count for result in case_results) / total
        if total
        else 0.0,
        avg_total_duration_ms=sum(result.metrics.total_duration_ms for result in case_results)
        / total
        if total
        else 0.0,
        avg_llm_duration_ms=sum(result.metrics.llm_duration_ms for result in case_results) / total
        if total
        else 0.0,
    )
