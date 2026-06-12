"""Contradiction lint rules."""

from uuid import uuid4

from backend.app.schemas.enums import (
    ClusterResolutionStatus,
    FactPolarity,
    FactType,
    LintFindingType,
)
from backend.app.schemas.lint import LintContext, LintFinding
from backend.app.services.lint_engine.matching import find_matching_facts
from backend.app.services.lint_engine.severity import severity_for_authority_contradiction


def _is_scope_contradiction(claim, fact) -> bool:
    if claim.claim_type == FactType.SCOPE_ITEM and claim.polarity == FactPolarity.POSITIVE:
        return (
            fact.fact_type == FactType.OUT_OF_SCOPE_ITEM
            and fact.polarity == FactPolarity.NEGATIVE
        )
    if claim.claim_type == FactType.OUT_OF_SCOPE_ITEM and claim.polarity == FactPolarity.NEGATIVE:
        return fact.fact_type == FactType.SCOPE_ITEM and fact.polarity == FactPolarity.POSITIVE
    return False


def _is_date_contradiction(claim, fact) -> bool:
    if claim.claim_type != FactType.DATE or fact.fact_type != FactType.DATE:
        return False
    claim_date = claim.attributes.date_value if claim.attributes else None
    fact_date = fact.attributes.date_value if fact.attributes else None
    return claim_date is not None and fact_date is not None and claim_date != fact_date


def run_contradiction_rules(context: LintContext) -> list[LintFinding]:
    findings: list[LintFinding] = []

    for claim in context.target_claims:
        if not claim.checkable:
            continue

        for fact in find_matching_facts(claim, context.project_facts):
            if not (_is_scope_contradiction(claim, fact) or _is_date_contradiction(claim, fact)):
                continue

            severity = severity_for_authority_contradiction(fact.source_authority_level)
            confidence = 0.9 if fact.source_authority_level >= 4 else 0.75

            related_cluster_ids = [
                cluster.id
                for cluster in context.fact_clusters
                if fact.id in cluster.fact_ids
            ]

            findings.append(
                LintFinding(
                    id=f"finding_{uuid4().hex}",
                    project_id=context.project_id,
                    target_document_id=claim.document_id,
                    finding_type=LintFindingType.REFERENCE_CONTRADICTION,
                    severity=severity,
                    confidence=confidence,
                    title="Target claim contradicts reference source",
                    message=(
                        "The target document conflicts with a reference fact on the same subject."
                    ),
                    target_claim_id=claim.id,
                    target_location=claim.location,
                    related_fact_ids=[fact.id],
                    related_fact_cluster_ids=related_cluster_ids,
                    related_source_profile_ids=[fact.source_profile_id],
                    target_quote=claim.location.quote,
                    reference_quotes=[fact.evidence.quote],
                    recommendation=(
                        "Resolve the conflict by aligning the target document with authoritative "
                        "reference sources or documenting an approved change."
                    ),
                    rule_id="contradiction.scope_opposite_polarity",
                )
            )

    for cluster in context.fact_clusters:
        if cluster.resolution_status != ClusterResolutionStatus.CONFLICT:
            continue

        for claim in context.target_claims:
            if not claim.checkable:
                continue
            if claim.normalized_subject != cluster.normalized_subject:
                continue

            findings.append(
                LintFinding(
                    id=f"finding_{uuid4().hex}",
                    project_id=context.project_id,
                    target_document_id=claim.document_id,
                    finding_type=LintFindingType.UNRESOLVED_REFERENCE_CONFLICT,
                    severity=severity_for_authority_contradiction(3),
                    confidence=0.7,
                    title="Unresolved reference conflict",
                    message=(
                        "Reference materials contain conflicting information on this subject, "
                        "and the target document relies on one side of that conflict."
                    ),
                    target_claim_id=claim.id,
                    target_location=claim.location,
                    related_fact_ids=cluster.fact_ids,
                    related_fact_cluster_ids=[cluster.id],
                    target_quote=claim.location.quote,
                    rule_id="contradiction.unresolved_reference_conflict",
                )
            )

    return findings
