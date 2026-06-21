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
    if "auctor" in lowered or "vendor" in lowered:
        return "auctor"
    if "northstar" in lowered or "client" in lowered:
        return "northstar"
    if "joint" in lowered or "both" in lowered:
        return "joint"
    return lowered.strip() or None


def _owner_from_text(text: str) -> str | None:
    """Infer the responsible party from a sentence when no owner attribute exists.

    Only returns a party when the sentence unambiguously names a single one. A
    sentence that mentions both parties (e.g. "Auctor will execute on behalf of
    Northstar") is ambiguous as to *ownership* and returns ``None`` so the caller
    falls back to the responsibility-party type.
    """
    lowered = text.lower()
    has_auctor = "auctor" in lowered or "vendor" in lowered
    has_northstar = "northstar" in lowered or "client" in lowered
    if has_auctor and not has_northstar:
        return "auctor"
    if has_northstar and not has_auctor:
        return "northstar"
    return None


def _resolve_owner(claim_or_fact_owner: str | None, text: str) -> str | None:
    return _normalize_owner(claim_or_fact_owner) or _owner_from_text(text)


def _is_excluded_by_fact(claim: TargetClaim, fact: ProjectFact) -> bool:
    """Claim commits to something the references explicitly mark out of scope.

    The exclusion signal is the reference ``fact_type`` being ``OUT_OF_SCOPE_ITEM``.
    We deliberately do NOT require the fact's polarity to be ``NEGATIVE``: an
    out-of-scope fact is an exclusion regardless of whether the extractor labelled
    "X is out of scope" as positive, neutral, or negative, and depending on that
    label was silently dropping real exclusions.

    Precision is preserved by requiring a shared *meaningful* anchor term (e.g.
    ``netsuite``, ``portal``) so a claim merely sharing a generic word like
    ``integration`` or ``access`` with an exclusion is not flagged. For example
    "Salesforce Sales Cloud object integration" must not match the "NetSuite
    billing integration" exclusion.
    """
    if claim.polarity == FactPolarity.NEGATIVE:
        return False
    if claim.claim_type not in COMMITMENT_CLAIM_TYPES:
        return False
    if fact.fact_type != FactType.OUT_OF_SCOPE_ITEM:
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

    Precision gate first: the claim and fact must share a meaningful subject/action
    term, which prevents comparing unrelated responsibilities (e.g. "Auctor will
    have access to a Salesforce admin" against "project governance").

    Recall: once the responsibilities are about the same thing, a conflict exists
    when the owners differ. Owners are resolved from the ``owner`` attribute or,
    when missing, inferred from the sentence text. If neither side yields a clear
    owner we fall back to the responsibility-party *type* (a client responsibility
    vs a team/vendor responsibility on the same subject) when the reference is
    authoritative -- this is how an "Auctor executes UAT" claim conflicts with a
    "Northstar owns UAT execution" signed fact even if owner attributes are absent.
    """
    if claim.claim_type not in RESPONSIBILITY_TYPES:
        return False
    if fact.fact_type not in RESPONSIBILITY_TYPES:
        return False
    if not subjects_share_meaningful_term(claim.normalized_subject, fact.normalized_subject):
        return False

    claim_owner = _resolve_owner(
        claim.attributes.owner if claim.attributes else None, claim.text
    )
    fact_owner = _resolve_owner(
        fact.attributes.owner if fact.attributes else None, fact.text
    )
    if claim_owner and fact_owner:
        if "joint" in {claim_owner, fact_owner}:
            return False
        return claim_owner != fact_owner

    # Owners not both resolvable: the responsibility-party type encodes which side
    # owns the work (client vs team/vendor). Differing parties on the same subject
    # is a conflict when the reference is signed/approved.
    return claim.claim_type != fact.fact_type and fact.source_authority_level >= 4


_CHANGE_CONTROL_FORMAL_TERMS = (
    "signed",
    "written change",
    "change order",
    "change request",
    "executive sponsor",
    "engagement manager",
    "both parties",
)
_CHANGE_CONTROL_INFORMAL_TERMS = (
    "backlog",
    "sprint",
    "project team",
    "verbal",
    "informal",
    "email",
    "agreement from",
)


def _is_change_control_weakening(claim: TargetClaim, fact: ProjectFact) -> bool:
    """Target weakens change control versus a signed/approved change-control rule.

    Fires when a change-control claim matches an authoritative change-control fact
    on the same subject but permits informal incorporation (sprint backlog, project
    team agreement) without the signed/written approval the reference requires.
    """
    if claim.claim_type != FactType.CHANGE_REQUEST:
        return False
    if fact.fact_type != FactType.CHANGE_REQUEST:
        return False
    if fact.fact_status not in APPROVED_STATUSES:
        return False
    if not subjects_share_meaningful_term(claim.normalized_subject, fact.normalized_subject):
        return False
    claim_text = claim.text.lower()
    has_informal = any(term in claim_text for term in _CHANGE_CONTROL_INFORMAL_TERMS)
    has_formal = any(term in claim_text for term in _CHANGE_CONTROL_FORMAL_TERMS)
    return has_informal and not has_formal


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
            rule_id="contradiction.responsibility_conflict",
        )

    # Priority 5: change control weakened versus a signed/approved rule.
    change_control_conflicts = [f for f in matches if _is_change_control_weakening(claim, f)]
    if change_control_conflicts:
        fact = _highest_authority_fact(change_control_conflicts)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title="Change-control language conflicts with signed process",
            message=(
                "The target document allows scope to change through informal agreement, "
                "but an authoritative reference requires signed/written change control."
            ),
            rule_id="contradiction.change_control_weakened",
            severity_floor=LintSeverity.HIGH,
        )

    # Priority 6: informal / requested item presented as approved scope.
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
