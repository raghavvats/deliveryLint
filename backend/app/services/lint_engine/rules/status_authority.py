"""Status and authority mismatch lint rules."""

from uuid import uuid4

from backend.app.schemas.enums import FactStatus, FactType, LintFindingType, LintSeverity
from backend.app.schemas.lint import LintContext, LintFinding
from backend.app.services.lint_engine.matching import find_matching_facts

APPROVED_STATUSES = {FactStatus.APPROVED, FactStatus.SIGNED, FactStatus.CONFIRMED}
REQUEST_STATUSES = {FactStatus.REQUESTED, FactStatus.PROPOSED, FactStatus.TENTATIVE}


def run_status_authority_rules(context: LintContext) -> list[LintFinding]:
    findings: list[LintFinding] = []

    for claim in context.target_claims:
        if not claim.checkable:
            continue

        if claim.claim_type != FactType.SCOPE_ITEM:
            continue

        matches = find_matching_facts(claim, context.project_facts)
        if not matches:
            continue

        has_approved = any(f.fact_status in APPROVED_STATUSES for f in matches)
        only_requests = all(
            f.fact_type in {FactType.CLIENT_REQUEST, FactType.CHANGE_REQUEST}
            and f.fact_status in REQUEST_STATUSES
            for f in matches
        )

        if only_requests and not has_approved:
            ref_quotes = [f.evidence.quote for f in matches]
            findings.append(
                LintFinding(
                    id=f"finding_{uuid4().hex}",
                    project_id=context.project_id,
                    target_document_id=claim.document_id,
                    finding_type=LintFindingType.STATUS_AUTHORITY_MISMATCH,
                    severity=LintSeverity.HIGH,
                    confidence=0.82,
                    title="Unapproved request presented as included scope",
                    message=(
                        "The target document treats this item as included scope, but matching "
                        "reference evidence only shows a client request or proposed change."
                    ),
                    target_claim_id=claim.id,
                    target_location=claim.location,
                    related_fact_ids=[f.id for f in matches],
                    related_source_profile_ids=list({f.source_profile_id for f in matches}),
                    target_quote=claim.location.quote,
                    reference_quotes=ref_quotes,
                    recommendation=(
                        "Mark this as a pending change request, remove it from committed scope, "
                        "or attach an approved change order."
                    ),
                    rule_id="authority.request_presented_as_scope",
                )
            )

    return findings
