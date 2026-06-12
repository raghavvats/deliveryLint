"""Correction UI response builder."""

from backend.app.schemas.correction_ui import (
    CorrectionFindingView,
    CorrectionSourceSummary,
    CorrectionSummary,
    CorrectionTargetDocument,
    CorrectionUIInput,
    CorrectionUIResponse,
)
from backend.app.schemas.enums import LintFindingType, LintSeverity, ReviewPriority
from backend.app.schemas.lint import LintFinding
from backend.app.schemas.source_profile import SourceProfile
from backend.app.schemas.target_parser import TargetParseResult
from backend.app.schemas.lint import RunLintOutput

PRIORITY_RANK = {
    ReviewPriority.NEEDS_FIX: 0,
    ReviewPriority.NEEDS_REVIEW: 1,
    ReviewPriority.QUALITY_SUGGESTION: 2,
    ReviewPriority.INFO: 3,
}


def classify_review_priority(finding: LintFinding) -> ReviewPriority:
    if finding.finding_type == LintFindingType.VAGUE_REQUIREMENT:
        return ReviewPriority.QUALITY_SUGGESTION

    if finding.finding_type == LintFindingType.MISSING_EXPECTED_CONTENT:
        if (
            finding.severity in {LintSeverity.CRITICAL, LintSeverity.HIGH}
            and finding.confidence >= 0.8
        ):
            return ReviewPriority.NEEDS_FIX
        return ReviewPriority.INFO

    if (
        finding.severity in {LintSeverity.CRITICAL, LintSeverity.HIGH}
        and finding.confidence >= 0.8
    ):
        return ReviewPriority.NEEDS_FIX

    if (
        finding.severity in {LintSeverity.CRITICAL, LintSeverity.HIGH}
        and finding.confidence < 0.8
    ):
        return ReviewPriority.NEEDS_REVIEW

    if finding.finding_type in {
        LintFindingType.UNSUPPORTED_TARGET_CLAIM,
        LintFindingType.UNRESOLVED_REFERENCE_CONFLICT,
        LintFindingType.STATUS_AUTHORITY_MISMATCH,
    }:
        return ReviewPriority.NEEDS_REVIEW

    if finding.finding_type in {
        LintFindingType.VAGUE_REQUIREMENT,
        LintFindingType.MISSING_ACCEPTANCE_CRITERIA,
        LintFindingType.MISSING_OWNER,
        LintFindingType.MISSING_DATE_VALUE,
        LintFindingType.UAT_TEST_MISSING_EXPECTED_RESULT,
        LintFindingType.UAT_COVERAGE_GAP,
    }:
        return ReviewPriority.QUALITY_SUGGESTION

    return ReviewPriority.INFO


def build_correction_source_summaries(
    finding: LintFinding,
    source_profile_by_id: dict[str, SourceProfile],
) -> list[CorrectionSourceSummary]:
    summaries: list[CorrectionSourceSummary] = []
    for source_profile_id in finding.related_source_profile_ids:
        profile = source_profile_by_id.get(source_profile_id)
        if profile is None:
            continue
        summaries.append(
            CorrectionSourceSummary(
                source_profile_id=profile.id,
                document_id=profile.document_id,
                doc_type=profile.doc_type,
                authority_level=profile.authority_level,
                status=profile.status,
                summary=profile.summary,
            )
        )
    return summaries


def build_correction_summary(findings: list[CorrectionFindingView]) -> CorrectionSummary:
    total = len(findings)

    needs_fix = sum(1 for f in findings if f.priority == ReviewPriority.NEEDS_FIX)
    needs_review = sum(1 for f in findings if f.priority == ReviewPriority.NEEDS_REVIEW)
    quality = sum(1 for f in findings if f.priority == ReviewPriority.QUALITY_SUGGESTION)
    info = sum(1 for f in findings if f.priority == ReviewPriority.INFO)

    critical = sum(1 for f in findings if f.severity == LintSeverity.CRITICAL)
    high = sum(1 for f in findings if f.severity == LintSeverity.HIGH)
    medium = sum(1 for f in findings if f.severity == LintSeverity.MEDIUM)
    low = sum(1 for f in findings if f.severity == LintSeverity.LOW)

    average_confidence = (
        sum(f.confidence for f in findings) / total if total > 0 else None
    )

    return CorrectionSummary(
        total_findings=total,
        needs_fix_count=needs_fix,
        needs_review_count=needs_review,
        quality_suggestion_count=quality,
        info_count=info,
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        low_count=low,
        average_confidence=average_confidence,
        has_blocking_issues=needs_fix > 0,
    )


def build_correction_ui_response(input: CorrectionUIInput) -> CorrectionUIResponse:
    return build_correction_ui_response_from_parts(
        project_id=input.project_id,
        target_document=input.target_document,
        target_parse_result=input.target_parse_result,
        lint_output=input.lint_output,
        source_profiles=input.source_profiles,
    )


def build_correction_ui_response_from_parts(
    *,
    project_id: str,
    target_document: CorrectionTargetDocument,
    target_parse_result: TargetParseResult,
    lint_output: RunLintOutput,
    source_profiles: list[SourceProfile],
) -> CorrectionUIResponse:
    source_profile_by_id = {profile.id: profile for profile in source_profiles}
    finding_views: list[CorrectionFindingView] = []

    for finding in lint_output.findings:
        finding_views.append(
            CorrectionFindingView(
                id=finding.id,
                priority=classify_review_priority(finding),
                finding_type=finding.finding_type,
                severity=finding.severity,
                confidence=finding.confidence,
                title=finding.title,
                message=finding.message,
                recommendation=finding.recommendation,
                target_quote=finding.target_quote,
                reference_quotes=finding.reference_quotes,
                target_location=finding.target_location,
                related_source_summaries=build_correction_source_summaries(
                    finding, source_profile_by_id
                ),
                rule_id=finding.rule_id,
            )
        )

    finding_views.sort(
        key=lambda view: (
            PRIORITY_RANK[view.priority],
            -view.confidence,
        )
    )

    summary = build_correction_summary(finding_views)

    return CorrectionUIResponse(
        project_id=project_id,
        target_document=target_document,
        target_profile=target_parse_result.target_profile,
        findings=finding_views,
        lint_warnings=lint_output.warnings,
        summary=summary,
    )
