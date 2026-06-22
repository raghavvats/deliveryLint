"""Tests for harness markdown export."""

from datetime import UTC, datetime

from backend.app.schemas.enums import DocType, LintFindingType
from backend.app.test_harness.export import export_filename, render_harness_run_markdown
from backend.app.test_harness.schemas import (
    ActualFindingSnapshot,
    ExpectedFindingResult,
    HarnessRunDetail,
    HarnessRunStatus,
    SuiteRunResult,
)


def test_render_harness_run_markdown_includes_missed_and_extra() -> None:
    detail = HarnessRunDetail(
        id=7,
        created_at=datetime(2026, 6, 22, tzinfo=UTC),
        status=HarnessRunStatus.COMPLETED,
        llm_provider="openai",
        suite_count=1,
        total_expected=2,
        total_caught=1,
        missed_count=1,
        recall_pct=50.0,
        suite_results=[
            SuiteRunResult(
                suite_id="deliverylint_suite_01_cpq_sow_scope_drift",
                suite_name="01 cpq sow scope drift",
                target_filename="target_draft_sow.md",
                target_doc_type=DocType.DRAFT_SOW,
                status="completed",
                expected_count=2,
                caught_count=1,
                missed_count=1,
                recall_pct=50.0,
                actual_finding_count=2,
                extra_finding_count=1,
                expected_results=[
                    ExpectedFindingResult(
                        index=1,
                        acceptable_types=[LintFindingType.REFERENCE_CONTRADICTION],
                        description="Target includes SAP integration.",
                        caught=True,
                        matched_finding_type=LintFindingType.REFERENCE_CONTRADICTION,
                        matched_title="SAP out of scope",
                        match_score=0.4,
                    ),
                    ExpectedFindingResult(
                        index=2,
                        acceptable_types=[LintFindingType.MISSING_DATE_VALUE],
                        description="Dependencies omit concrete dates.",
                        caught=False,
                    ),
                ],
                extra_findings=[
                    ActualFindingSnapshot(
                        id="f-extra",
                        finding_type=LintFindingType.VAGUE_REQUIREMENT,
                        title="Vague performance language",
                        message="Target uses seamless performance wording.",
                    )
                ],
            )
        ],
    )
    markdown = render_harness_run_markdown(detail)
    assert "Overall recall: **50.0%**" in markdown
    assert "### Missed answer-key items (1)" in markdown
    assert "**MISSED**" in markdown
    assert "Dependencies omit concrete dates." in markdown
    assert "### Extra findings (1)" in markdown
    assert "Vague performance language" in markdown
    assert export_filename(7) == "deliverylint-harness-run-7.md"
