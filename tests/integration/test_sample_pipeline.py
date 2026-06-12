import pytest

from backend.app.schemas.enums import ReviewPriority
from backend.app.services.correction_ui import classify_review_priority
from backend.app.schemas.enums import LintFindingType, LintSeverity
from backend.app.schemas.lint import LintFinding


def test_classify_needs_fix() -> None:
    finding = LintFinding(
        id="f1",
        project_id="p1",
        target_document_id="t1",
        finding_type=LintFindingType.REFERENCE_CONTRADICTION,
        severity=LintSeverity.CRITICAL,
        confidence=0.9,
        title="t",
        message="m",
        rule_id="r",
    )
    assert classify_review_priority(finding) == ReviewPriority.NEEDS_FIX


@pytest.mark.asyncio
async def test_sample_pipeline_priorities() -> None:
    from backend.app.pipeline.run_pipeline import run_full_pipeline

    result = await run_full_pipeline()
    priorities = {f.priority for f in result.correction_ui_response.findings}
    assert ReviewPriority.NEEDS_FIX in priorities
    assert ReviewPriority.NEEDS_REVIEW in priorities
    assert ReviewPriority.QUALITY_SUGGESTION in priorities
    assert ReviewPriority.INFO in priorities
    assert result.correction_ui_response.summary.total_findings > 0
