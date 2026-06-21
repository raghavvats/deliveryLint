"""Rubric quality lint rules."""

from uuid import uuid4

from backend.app.schemas.enums import DocType, FactType, LintFindingType, LintSeverity
from backend.app.schemas.lint import LintContext, LintFinding
from backend.app.services.lint_engine.matching import (
    contains_vague_language,
    is_actionable_task,
    mentions_explicit_owner,
    subjects_match,
    uat_test_has_expected_result,
)

# Claim types for which a missing owner is only meaningful if the item is an
# actionable task rather than a passive assumption/dependency statement.
_ACTIONABLE_REQUIRED_FOR_OWNER = {FactType.DEPENDENCY}


def run_rubric_quality_rules(context: LintContext) -> list[LintFinding]:
    findings: list[LintFinding] = []
    claims = context.target_claims

    # Vague language is a quality problem in any checkable claim, not just scope /
    # requirements. The curated VAGUE_TERMS list keeps this from being noisy, while
    # checking every claim type ensures statements like "fast, user-friendly, and
    # seamless" are caught regardless of how the extractor typed them.
    for claim in claims:
        if claim.checkable and contains_vague_language(claim.text):
            findings.append(
                LintFinding(
                    id=f"finding_{uuid4().hex}",
                    project_id=context.project_id,
                    target_document_id=claim.document_id,
                    finding_type=LintFindingType.VAGUE_REQUIREMENT,
                    severity=LintSeverity.MEDIUM,
                    confidence=0.7,
                    title="Vague requirement",
                    message=(
                        "This requirement uses vague language that may be difficult to test or verify."
                    ),
                    target_claim_id=claim.id,
                    target_location=claim.location,
                    target_quote=claim.location.quote,
                    rule_id="rubric.vague_requirement",
                )
            )

        if claim.claim_type == FactType.REQUIREMENT:
            has_ac = any(
                c.claim_type == FactType.ACCEPTANCE_CRITERIA
                and subjects_match(c.normalized_subject, claim.normalized_subject)
                for c in claims
            )
            if not has_ac:
                findings.append(
                    LintFinding(
                        id=f"finding_{uuid4().hex}",
                        project_id=context.project_id,
                        target_document_id=claim.document_id,
                        finding_type=LintFindingType.MISSING_ACCEPTANCE_CRITERIA,
                        severity=LintSeverity.MEDIUM,
                        confidence=0.65,
                        title="Missing acceptance criteria",
                        message="This requirement has no matching acceptance criteria claim.",
                        target_claim_id=claim.id,
                        target_location=claim.location,
                        target_quote=claim.location.quote,
                        rule_id="rubric.missing_acceptance_criteria",
                    )
                )

        if claim.claim_type in {
            FactType.CLIENT_RESPONSIBILITY,
            FactType.TEAM_RESPONSIBILITY,
            FactType.MILESTONE,
            FactType.DEPENDENCY,
        }:
            owner = claim.attributes.owner if claim.attributes else None
            owner_is_explicit_in_text = mentions_explicit_owner(claim.text)
            needs_actionable = claim.claim_type in _ACTIONABLE_REQUIRED_FOR_OWNER
            is_actionable = is_actionable_task(claim.text)
            should_flag_missing_owner = (
                not owner
                and not owner_is_explicit_in_text
                and not (needs_actionable and not is_actionable)
            )
            if should_flag_missing_owner:
                findings.append(
                    LintFinding(
                        id=f"finding_{uuid4().hex}",
                        project_id=context.project_id,
                        target_document_id=claim.document_id,
                        finding_type=LintFindingType.MISSING_OWNER,
                        severity=LintSeverity.LOW,
                        confidence=0.8,
                        title="Missing owner",
                        message="This claim appears to lack an assigned owner.",
                        target_claim_id=claim.id,
                        target_location=claim.location,
                        target_quote=claim.location.quote,
                        rule_id="rubric.missing_owner",
                    )
                )

        if claim.claim_type == FactType.DATE:
            date_value = claim.attributes.date_value if claim.attributes else None
            if date_value is None:
                findings.append(
                    LintFinding(
                        id=f"finding_{uuid4().hex}",
                        project_id=context.project_id,
                        target_document_id=claim.document_id,
                        finding_type=LintFindingType.MISSING_DATE_VALUE,
                        severity=LintSeverity.MEDIUM,
                        confidence=0.85,
                        title="Missing date value",
                        message="This date-related claim lacks a concrete date value.",
                        target_claim_id=claim.id,
                        target_location=claim.location,
                        target_quote=claim.location.quote,
                        rule_id="rubric.missing_date_value",
                    )
                )

        if claim.claim_type == FactType.UAT_TEST and not uat_test_has_expected_result(claim):
            findings.append(
                LintFinding(
                    id=f"finding_{uuid4().hex}",
                    project_id=context.project_id,
                    target_document_id=claim.document_id,
                    finding_type=LintFindingType.UAT_TEST_MISSING_EXPECTED_RESULT,
                    severity=LintSeverity.MEDIUM,
                    confidence=0.75,
                    title="UAT test missing expected result",
                    message="This UAT test claim does not include a clear expected result.",
                    target_claim_id=claim.id,
                    target_location=claim.location,
                    target_quote=claim.location.quote,
                    rule_id="rubric.uat_test_missing_expected_result",
                )
            )

    if context.target_profile.doc_type == DocType.UAT_PLAN:
        requirement_subjects = {
            f.normalized_subject
            for f in context.project_facts
            if f.fact_type == FactType.REQUIREMENT
        }
        uat_subjects = {
            c.normalized_subject for c in claims if c.claim_type == FactType.UAT_TEST
        }
        for subject in requirement_subjects:
            if subject not in uat_subjects:
                findings.append(
                    LintFinding(
                        id=f"finding_{uuid4().hex}",
                        project_id=context.project_id,
                        target_document_id=context.target_profile.document_id,
                        finding_type=LintFindingType.UAT_COVERAGE_GAP,
                        severity=LintSeverity.LOW,
                        confidence=0.55,
                        title="UAT coverage gap",
                        message=(
                            f"Reference requirement '{subject}' has no matching UAT test "
                            "by normalized subject."
                        ),
                        rule_id="rubric.uat_coverage_gap",
                    )
                )

    return findings
