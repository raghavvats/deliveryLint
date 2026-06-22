"""Run DeliveryLint test suites and score against answer keys."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from uuid import uuid4

from backend.app.config.settings import get_settings
from backend.app.pipeline.run_pipeline import run_custom_pipeline
from backend.app.schemas.upload import CustomLintRequest
from backend.app.services.llm_client import create_llm_client
from backend.app.test_harness.scorer import recall_pct, score_expected_findings
from backend.app.test_harness.schemas import (
    HarnessRunDetail,
    HarnessRunStatus,
    HarnessRunSummary,
    SuiteRunResult,
    TestSuiteDefinition,
)
from backend.app.test_harness.suite_loader import discover_suites, load_suite_documents


async def run_suite(suite: TestSuiteDefinition) -> SuiteRunResult:
    started = time.perf_counter()
    try:
        target, references = load_suite_documents(suite)
        llm_client = create_llm_client(use_fixtures=False)
        request = CustomLintRequest(
            project_id=f"test_{suite.id}_{uuid4().hex[:8]}",
            run_name=f"Harness: {suite.name}",
            target=target,
            target_doc_type=suite.target_doc_type,
            references=references,
        )
        pipeline_result = await run_custom_pipeline(request, llm_client=llm_client)
        actual_findings = pipeline_result.correction_ui_response.findings
        expected_results, extra_findings = score_expected_findings(
            suite.expected_findings,
            actual_findings,
        )
        caught_count = sum(1 for item in expected_results if item.caught)
        expected_count = len(expected_results)
        duration_ms = int((time.perf_counter() - started) * 1000)
        return SuiteRunResult(
            suite_id=suite.id,
            suite_name=suite.name,
            target_filename=suite.target_filename,
            target_doc_type=suite.target_doc_type,
            status="completed",
            expected_count=expected_count,
            caught_count=caught_count,
            missed_count=expected_count - caught_count,
            recall_pct=recall_pct(caught_count, expected_count),
            actual_finding_count=len(actual_findings),
            extra_finding_count=len(extra_findings),
            expected_results=expected_results,
            extra_findings=extra_findings,
            duration_ms=duration_ms,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return SuiteRunResult(
            suite_id=suite.id,
            suite_name=suite.name,
            target_filename=suite.target_filename,
            target_doc_type=suite.target_doc_type,
            status="failed",
            error_message=str(exc),
            expected_count=len(suite.expected_findings),
            duration_ms=duration_ms,
        )


async def run_harness(
    suite_ids: list[str] | None = None,
) -> HarnessRunDetail:
    all_suites = discover_suites()
    if suite_ids:
        selected = {suite_id: suite for suite_id, suite in ((s.id, s) for s in all_suites)}
        suites = [selected[suite_id] for suite_id in suite_ids if suite_id in selected]
        missing = [suite_id for suite_id in suite_ids if suite_id not in selected]
        if missing:
            msg = f"Unknown suite id(s): {', '.join(missing)}"
            raise ValueError(msg)
    else:
        suites = all_suites

    if not suites:
        msg = "No test suites found under testFiles/"
        raise ValueError(msg)

    suite_results: list[SuiteRunResult] = []
    for suite in suites:
        suite_results.append(await run_suite(suite))

    total_expected = sum(result.expected_count for result in suite_results)
    total_caught = sum(result.caught_count for result in suite_results)
    failed = any(result.status == "failed" for result in suite_results)

    return HarnessRunDetail(
        id=0,
        created_at=datetime.now(UTC),
        status=HarnessRunStatus.FAILED if failed else HarnessRunStatus.COMPLETED,
        llm_provider=get_settings().llm_provider,
        suite_count=len(suite_results),
        total_expected=total_expected,
        total_caught=total_caught,
        missed_count=total_expected - total_caught,
        recall_pct=recall_pct(total_caught, total_expected),
        suite_results=suite_results,
    )


def harness_detail_to_summary(detail: HarnessRunDetail) -> HarnessRunSummary:
    return HarnessRunSummary(
        id=detail.id,
        created_at=detail.created_at,
        status=detail.status,
        llm_provider=detail.llm_provider,
        suite_count=detail.suite_count,
        total_expected=detail.total_expected,
        total_caught=detail.total_caught,
        recall_pct=detail.recall_pct,
        error_message=detail.error_message,
    )
