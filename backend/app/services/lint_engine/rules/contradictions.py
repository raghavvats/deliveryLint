"""Cluster-level contradiction lint rules.

Per-claim contradictions (out-of-scope inclusion, date conflicts, responsibility
conflicts) live in ``claim_classification`` so that each claim receives a single
prioritized finding. This module only handles conflicts that exist *between
reference documents* (a fact cluster with conflicting polarities) that the target
then relies on.
"""

from uuid import uuid4

from backend.app.schemas.enums import ClusterResolutionStatus, LintFindingType
from backend.app.schemas.lint import LintContext, LintFinding
from backend.app.services.lint_engine.severity import severity_for_authority_contradiction


def run_contradiction_rules(context: LintContext) -> list[LintFinding]:
    findings: list[LintFinding] = []

    for cluster in context.fact_clusters:
        if cluster.resolution_status != ClusterResolutionStatus.CONFLICT:
            continue

        for claim in context.target_claims:
            if not claim.checkable:
                continue
            if claim.normalized_subject != cluster.normalized_subject:
                continue

            cluster_facts = [
                fact
                for fact in context.project_facts
                if fact.id in cluster.fact_ids
            ]
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
                    related_source_profile_ids=list(
                        {fact.source_profile_id for fact in cluster_facts}
                    ),
                    target_quote=claim.location.quote,
                    reference_quotes=[fact.evidence.quote for fact in cluster_facts],
                    rule_id="contradiction.unresolved_reference_conflict",
                )
            )

    return findings
