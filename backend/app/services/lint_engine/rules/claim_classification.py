"""Prioritized per-claim classification rules.

A single target claim should receive at most one *primary* grounding finding.
Historically the engine ran independent grounding / contradiction / status rules
and, because subject matching was brittle, ``unsupported_target_claim`` became
the de-facto default for everything. This module instead evaluates each claim
against its matching reference facts in a fixed priority order and emits the
strongest applicable finding, falling back to ``unsupported_target_claim`` only
when nothing stronger applies.

Priority order (strongest first):
    1. Explicit contradiction: claim asserts something the references explicitly
       list as out of scope / excluded.
    2. Opposite-polarity scope contradiction.
    3. Date conflict against an authoritative date.
    4. Responsibility / owner conflict.
    5. Informal/requested item presented as approved scope
       (``status_authority_mismatch``).
    6. Supported by reference evidence -> no finding.
    7. Unsupported target claim (fallback only).
"""

from uuid import uuid4

from backend.app.schemas.enums import (
    FactPolarity,
    FactStatus,
    FactType,
    LintFindingType,
    LintSeverity,
)
from backend.app.schemas.lint import LintContext, LintFinding
from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.target_document import TargetClaim
from backend.app.services.lint_engine.matching import (
    find_matching_facts,
    has_reference_coverage_for_claim,
    subjects_share_meaningful_term,
)
from backend.app.services.lint_engine.severity import severity_for_authority_contradiction

APPROVED_STATUSES = {FactStatus.APPROVED, FactStatus.SIGNED, FactStatus.CONFIRMED}
REQUEST_FACT_TYPES = {FactType.CLIENT_REQUEST, FactType.CHANGE_REQUEST}
REQUEST_STATUSES = {FactStatus.REQUESTED, FactStatus.PROPOSED, FactStatus.TENTATIVE}

# Claim types that assert the target intends to *do* / *deliver* / *accept* work.
COMMITMENT_CLAIM_TYPES = {
    FactType.SCOPE_ITEM,
    FactType.DELIVERABLE,
    FactType.ACCEPTANCE_CRITERIA,
    FactType.REQUIREMENT,
    FactType.UAT_TEST,
    FactType.SYSTEM_OR_INTEGRATION,
    FactType.DEPENDENCY,
}

RESPONSIBILITY_TYPES = {FactType.CLIENT_RESPONSIBILITY, FactType.TEAM_RESPONSIBILITY}


def _highest_authority_fact(facts: list[ProjectFact]) -> ProjectFact:
    return max(
        facts,
        key=lambda f: (f.source_authority_level, f.extraction_confidence),
    )


def _normalize_owner(owner: str | None) -> str | None:
    if not owner:
        return None
    lowered = owner.lower()
    if "auctor" in lowered:
        return "auctor"
    if "northstar" in lowered or "client" in lowered:
        return "northstar"
    if "joint" in lowered or "both" in lowered:
        return "joint"
    return lowered.strip() or None


def _is_excluded_by_fact(claim: TargetClaim, fact: ProjectFact) -> bool:
    """Claim commits to something the references explicitly mark out of scope.

    Requires a shared *meaningful* anchor term (e.g. ``netsuite``, ``portal``) so
    that a claim merely sharing a generic word like ``integration`` or ``access``
    with an exclusion is not flagged. For example "Salesforce Sales Cloud object
    integration" must not match the "NetSuite billing integration" exclusion.
    """
    if claim.polarity == FactPolarity.NEGATIVE:
        return False
    if claim.claim_type not in COMMITMENT_CLAIM_TYPES:
        return False
    if not (
        fact.fact_type == FactType.OUT_OF_SCOPE_ITEM
        and fact.polarity == FactPolarity.NEGATIVE
    ):
        return False
    return subjects_share_meaningful_term(claim.normalized_subject, fact.normalized_subject)


def _is_polarity_scope_conflict(claim: TargetClaim, fact: ProjectFact) -> bool:
    """Claim says out-of-scope but an authoritative reference says in-scope."""
    if claim.claim_type == FactType.OUT_OF_SCOPE_ITEM and claim.polarity == FactPolarity.NEGATIVE:
        return fact.fact_type == FactType.SCOPE_ITEM and fact.polarity == FactPolarity.POSITIVE
    return False


def _is_date_conflict(claim: TargetClaim, fact: ProjectFact) -> bool:
    if claim.claim_type != FactType.DATE or fact.fact_type != FactType.DATE:
        return False
    claim_date = claim.attributes.date_value if claim.attributes else None
    fact_date = fact.attributes.date_value if fact.attributes else None
    if claim_date is None or fact_date is None or claim_date == fact_date:
        return False
    claim_dt = claim.attributes.date_type if claim.attributes else None
    fact_dt = fact.attributes.date_type if fact.attributes else None
    # If both sides label the date type, require them to agree before calling it a
    # conflict (a kickoff date differing from a go-live date is not a conflict).
    if claim_dt is not None and fact_dt is not None and claim_dt != fact_dt:
        return False
    return True


def _is_responsibility_conflict(claim: TargetClaim, fact: ProjectFact) -> bool:
    """Owner conflict on the *same* responsibility.

    Both sides must name an owner, the owners must genuinely differ (and not be
    joint), and the claim and fact must share a meaningful subject/action term.
    The last condition prevents comparing unrelated responsibilities, e.g.
    "Auctor will have access to a Salesforce admin" against "project management".
    """
    if claim.claim_type not in RESPONSIBILITY_TYPES:
        return False
    if fact.fact_type not in RESPONSIBILITY_TYPES:
        return False
    claim_owner = _normalize_owner(claim.attributes.owner if claim.attributes else None)
    fact_owner = _normalize_owner(fact.attributes.owner if fact.attributes else None)
    if not (claim_owner and fact_owner):
        return False
    if "joint" in {claim_owner, fact_owner}:
        return False
    if claim_owner == fact_owner:
        return False
    return subjects_share_meaningful_term(claim.normalized_subject, fact.normalized_subject)


def _related_cluster_ids(context: LintContext, fact: ProjectFact) -> list[str]:
    return [
        cluster.id for cluster in context.fact_clusters if fact.id in cluster.fact_ids
    ]


def _contradiction_finding(
    *,
    context: LintContext,
    claim: TargetClaim,
    fact: ProjectFact,
    title: str,
    message: str,
    recommendation: str,
    rule_id: str,
    severity_floor: LintSeverity | None = None,
) -> LintFinding:
    # Severity tracks reference authority, but only when the subject match is
    # high-confidence (a shared meaningful anchor term). A weak/incidental match
    # must not become critical just because the reference is signed/high-authority.
    high_confidence = subjects_share_meaningful_term(
        claim.normalized_subject, fact.normalized_subject
    )
    if high_confidence:
        severity = severity_for_authority_contradiction(fact.source_authority_level)
        if severity_floor is not None and _severity_rank(severity) < _severity_rank(severity_floor):
            severity = severity_floor
        confidence = 0.9 if fact.source_authority_level >= 4 else 0.75
    else:
        severity = LintSeverity.MEDIUM
        confidence = 0.6
    return LintFinding(
        id=f"finding_{uuid4().hex}",
        project_id=context.project_id,
        target_document_id=claim.document_id,
        finding_type=LintFindingType.REFERENCE_CONTRADICTION,
        severity=severity,
        confidence=confidence,
        title=title,
        message=message,
        target_claim_id=claim.id,
        target_location=claim.location,
        related_fact_ids=[fact.id],
        related_fact_cluster_ids=_related_cluster_ids(context, fact),
        related_source_profile_ids=[fact.source_profile_id],
        target_quote=claim.location.quote,
        reference_quotes=[fact.evidence.quote],
        recommendation=recommendation,
        rule_id=rule_id,
    )


def _severity_rank(severity: LintSeverity) -> int:
    return {
        LintSeverity.CRITICAL: 4,
        LintSeverity.HIGH: 3,
        LintSeverity.MEDIUM: 2,
        LintSeverity.LOW: 1,
    }[severity]


def _unsupported_finding(context: LintContext, claim: TargetClaim) -> LintFinding:
    return LintFinding(
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


def _classify_claim(context: LintContext, claim: TargetClaim) -> LintFinding | None:
    matches = find_matching_facts(claim, context.project_facts)

    if not matches:
        if not has_reference_coverage_for_claim(claim, context.source_profiles):
            return None
        return _unsupported_finding(context, claim)

    # Priority 1: explicit out-of-scope / exclusion contradiction.
    excluded = [f for f in matches if _is_excluded_by_fact(claim, f)]
    if excluded:
        fact = _highest_authority_fact(excluded)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title="Target includes work that references explicitly exclude",
            message=(
                "The target document treats this item as in scope, but an authoritative "
                "reference document explicitly lists it as out of scope / excluded."
            ),
            recommendation=(
                "Remove this item from committed scope or obtain a signed change order "
                "before presenting it as included work."
            ),
            rule_id="contradiction.target_includes_excluded_item",
            severity_floor=LintSeverity.HIGH,
        )

    # Priority 2: opposite-polarity scope contradiction.
    polarity_conflicts = [f for f in matches if _is_polarity_scope_conflict(claim, f)]
    if polarity_conflicts:
        fact = _highest_authority_fact(polarity_conflicts)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title="Target claim contradicts reference scope",
            message="The target document conflicts with a reference fact on the same subject.",
            recommendation=(
                "Resolve the conflict by aligning the target document with authoritative "
                "reference sources or documenting an approved change."
            ),
            rule_id="contradiction.scope_opposite_polarity",
        )

    # Priority 3: date conflict.
    date_conflicts = [f for f in matches if _is_date_conflict(claim, f)]
    if date_conflicts:
        fact = _highest_authority_fact(date_conflicts)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title="Target date conflicts with reference source",
            message=(
                "The target document uses a date that conflicts with an authoritative reference."
            ),
            recommendation=(
                "Align the date with the signed/approved reference or document an "
                "approved change to the schedule."
            ),
            rule_id="contradiction.date_conflict",
        )

    # Priority 4: responsibility / owner conflict.
    responsibility_conflicts = [f for f in matches if _is_responsibility_conflict(claim, f)]
    if responsibility_conflicts:
        fact = _highest_authority_fact(responsibility_conflicts)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title="Responsibility assignment conflicts with reference source",
            message=(
                "The target document assigns this responsibility to a different owner than "
                "the authoritative reference documents do."
            ),
            recommendation=(
                "Reassign the responsibility to match the signed/approved reference, or "
                "document an approved change of ownership."
            ),
            rule_id="contradiction.responsibility_conflict",
        )

    # Priority 5: informal / requested item presented as approved scope.
    if claim.claim_type in COMMITMENT_CLAIM_TYPES:
        has_approving_support = any(
            f.fact_status in APPROVED_STATUSES
            or (
                f.fact_type not in REQUEST_FACT_TYPES
                and f.polarity != FactPolarity.NEGATIVE
            )
            for f in matches
        )
        only_requests = all(
            f.fact_type in REQUEST_FACT_TYPES or f.fact_status in REQUEST_STATUSES
            for f in matches
        )
        if only_requests and not has_approving_support:
            ref_quotes = [f.evidence.quote for f in matches]
            return LintFinding(
                id=f"finding_{uuid4().hex}",
                project_id=context.project_id,
                target_document_id=claim.document_id,
                finding_type=LintFindingType.STATUS_AUTHORITY_MISMATCH,
                severity=LintSeverity.HIGH,
                confidence=0.82,
                title="Unapproved request presented as included scope",
                message=(
                    "The target document treats this item as included scope, but matching "
                    "reference evidence only shows an informal client request or proposed change."
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

    # Otherwise the claim is supported by matching reference evidence -> no finding.
    return None


def run_claim_classification_rules(context: LintContext) -> list[LintFinding]:
    findings: list[LintFinding] = []
    for claim in context.target_claims:
        if not claim.checkable:
            continue
        finding = _classify_claim(context, claim)
        if finding is not None:
            findings.append(finding)
    return findings
