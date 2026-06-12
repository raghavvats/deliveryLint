"""Grounding lint rules."""

from uuid import uuid4

from backend.app.schemas.enums import LintFindingType, LintSeverity
from backend.app.schemas.lint import LintContext, LintFinding
from backend.app.services.lint_engine.matching import (
    find_matching_facts,
    has_reference_coverage_for_claim,
)


def run_grounding_rules(context: LintContext) -> list[LintFinding]:
    findings: list[LintFinding] = []

    for claim in context.target_claims:
        if not claim.checkable:
            continue

        if not has_reference_coverage_for_claim(claim, context.source_profiles):
            continue

        matches = find_matching_facts(claim, context.project_facts)
        if matches:
            continue

        findings.append(
            LintFinding(
                id=f"finding_{uuid4().hex}",
                project_id=context.project_id,
                target_document_id=claim.document_id,
                finding_type=LintFindingType.UNSUPPORTED_TARGET_CLAIM,
                severity=LintSeverity.MEDIUM,
                confidence=0.75,
                title="Unsupported target claim",
                message=(
                    "This claim is not supported by the uploaded reference materials. "
                    "This does not prove the claim is wrong, but it should be verified."
                ),
                target_claim_id=claim.id,
                target_location=claim.location,
                target_quote=claim.location.quote,
                recommendation="Verify this claim against official scope sources before relying on it.",
                rule_id="grounding.unsupported_target_claim",
            )
        )

    return findings
