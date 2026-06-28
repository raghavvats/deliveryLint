"""Correction UI response builder."""

from backend.app.domain.span_resolution import (
    _normalize_quote_for_match,
    resolve_evidence_span,
    resolve_target_location,
)
from backend.app.schemas.correction_ui import (
    CorrectionFindingView,
    CorrectionReferenceDocument,
    CorrectionSourceSummary,
    CorrectionSummary,
    CorrectionTargetDocument,
    CorrectionUIInput,
    CorrectionUIResponse,
    ReferenceEvidenceView,
)
from backend.app.schemas.enums import DocType, LintFindingType, LintSeverity, ReviewPriority
from backend.app.schemas.lint import (
    LintEngineWarning,
    LintEngineWarningCode,
    LintFinding,
    RunLintOutput,
)
from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.source_profile import SourceProfile
from backend.app.schemas.target_parser import (
    TargetParseResult,
    TargetParseWarningCode,
)

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
        LintFindingType.REFERENCE_CONTRADICTION,
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


def _find_fact_by_quote(quote: str, facts: list[ProjectFact]) -> ProjectFact | None:
    normalized = _normalize_quote_for_match(quote)
    if not normalized:
        return None
    for fact in facts:
        if _normalize_quote_for_match(fact.evidence.quote) == normalized:
            return fact
    for fact in facts:
        if normalized in _normalize_quote_for_match(fact.evidence.quote):
            return fact
    return None


def build_reference_evidence(
    finding: LintFinding,
    fact_by_id: dict[str, ProjectFact],
    reference_text_by_document_id: dict[str, str],
    *,
    all_facts: list[ProjectFact] | None = None,
) -> list[ReferenceEvidenceView]:
    evidence_views: list[ReferenceEvidenceView] = []
    seen_fact_ids: set[str] = set()
    facts = all_facts or list(fact_by_id.values())

    def add_fact_evidence(fact: ProjectFact) -> None:
        if fact.id in seen_fact_ids:
            return
        seen_fact_ids.add(fact.id)
        ref_text = reference_text_by_document_id.get(fact.document_id, "")
        resolved = resolve_evidence_span(ref_text, fact.evidence) if ref_text else fact.evidence
        evidence_views.append(
            ReferenceEvidenceView(
                fact_id=fact.id,
                document_id=fact.document_id,
                source_profile_id=fact.source_profile_id,
                quote=resolved.quote,
                location=resolved,
            )
        )

    for fact_id in finding.related_fact_ids:
        fact = fact_by_id.get(fact_id)
        if fact is not None:
            add_fact_evidence(fact)

    if not evidence_views and finding.reference_quotes:
        for quote in finding.reference_quotes:
            fact = _find_fact_by_quote(quote, facts)
            if fact is not None:
                add_fact_evidence(fact)

    if not evidence_views and finding.related_source_profile_ids:
        profile_ids = set(finding.related_source_profile_ids)
        for fact in facts:
            if fact.source_profile_id in profile_ids:
                add_fact_evidence(fact)

    return evidence_views


def build_reference_documents(
    source_profiles: list[SourceProfile],
    reference_text_by_document_id: dict[str, str],
    reference_filenames_by_document_id: dict[str, str | None] | None = None,
) -> list[CorrectionReferenceDocument]:
    documents: list[CorrectionReferenceDocument] = []
    seen: set[str] = set()
    ref_filenames = reference_filenames_by_document_id or {}
    for profile in source_profiles:
        if profile.document_id in seen:
            continue
        text = reference_text_by_document_id.get(profile.document_id)
        if text is None:
            continue
        seen.add(profile.document_id)
        documents.append(
            CorrectionReferenceDocument(
                document_id=profile.document_id,
                filename=ref_filenames.get(profile.document_id),
                text=text,
                doc_type=profile.doc_type,
                source_profile_id=profile.id,
            )
        )

    for document_id, text in reference_text_by_document_id.items():
        if document_id in seen or not text:
            continue
        documents.append(
            CorrectionReferenceDocument(
                document_id=document_id,
                filename=ref_filenames.get(document_id),
                text=text,
                doc_type=DocType.UNKNOWN,
                source_profile_id=document_id,
            )
        )
    return documents


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
        project_facts=input.project_facts,
    )


def build_correction_ui_response_from_parts(
    *,
    project_id: str,
    target_document: CorrectionTargetDocument,
    target_parse_result: TargetParseResult,
    lint_output: RunLintOutput,
    source_profiles: list[SourceProfile],
    project_facts: list[ProjectFact] | None = None,
    reference_text_by_document_id: dict[str, str] | None = None,
    reference_filenames_by_document_id: dict[str, str | None] | None = None,
) -> CorrectionUIResponse:
    source_profile_by_id = {profile.id: profile for profile in source_profiles}
    fact_by_id = {fact.id: fact for fact in (project_facts or [])}
    facts = project_facts or []
    ref_texts = reference_text_by_document_id or {}
    ref_filenames = reference_filenames_by_document_id or {}

    finding_views: list[CorrectionFindingView] = []
    target_text = target_document.text

    for finding in lint_output.findings:
        resolved_location = resolve_target_location(target_text, finding.target_location)
        finding_views.append(
            CorrectionFindingView(
                id=finding.id,
                priority=classify_review_priority(finding),
                finding_type=finding.finding_type,
                severity=finding.severity,
                confidence=finding.confidence,
                title=finding.title,
                message=finding.message,
                target_quote=finding.target_quote,
                reference_quotes=finding.reference_quotes,
                target_location=resolved_location,
                related_source_summaries=build_correction_source_summaries(
                    finding, source_profile_by_id
                ),
                reference_evidence=build_reference_evidence(
                    finding,
                    fact_by_id,
                    ref_texts,
                    all_facts=facts,
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

    reference_documents = build_reference_documents(
        source_profiles, ref_texts, ref_filenames
    )

    warnings = list(lint_output.warnings)
    warnings.extend(_target_parse_ui_warnings(target_parse_result))

    return CorrectionUIResponse(
        project_id=project_id,
        target_document=target_document,
        target_profile=target_parse_result.target_profile,
        reference_documents=reference_documents,
        findings=finding_views,
        lint_warnings=warnings,
        summary=summary,
    )


def _target_parse_ui_warnings(
    target_parse_result: TargetParseResult,
) -> list[LintEngineWarning]:
    """Forward target-parse warnings that the reviewer needs to see in the UI.

    Currently only document truncation is surfaced here; other parse warnings are
    already reflected by target quality flags.
    """
    forwarded: list[LintEngineWarning] = []
    for warning in target_parse_result.warnings:
        if warning.code == TargetParseWarningCode.DOCUMENT_TRUNCATED:
            forwarded.append(
                LintEngineWarning(
                    code=LintEngineWarningCode.DOCUMENT_TRUNCATED,
                    message=warning.message,
                )
            )
    return forwarded
