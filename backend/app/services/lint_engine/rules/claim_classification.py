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
    5. Change-control weakening (``reference_contradiction``).
    6. Informal/requested item presented as approved scope
       (``status_authority_mismatch``).
    7. Supported by reference evidence -> no finding.
    8. Unsupported target claim (fallback only).
"""

from __future__ import annotations

import re
from uuid import uuid4

from backend.app.domain.attribute_enrichment import extract_iso_date
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
from backend.app.services.lint_engine.finding_copy import (
    authority_mismatch_copy,
    change_control_copy,
    date_conflict_copy,
    exclusion_contradiction_copy,
    responsibility_conflict_copy,
    unsupported_claim_copy,
)
from backend.app.services.lint_engine.matching import (
    find_exclusion_facts,
    find_matching_facts,
    has_reference_coverage_for_claim,
    subjects_share_meaningful_term,
    text_anchors_claim_to_fact,
)
from backend.app.services.lint_engine.severity import severity_for_authority_contradiction

APPROVED_STATUSES = {FactStatus.APPROVED, FactStatus.SIGNED, FactStatus.CONFIRMED}
REQUEST_FACT_TYPES = {FactType.CLIENT_REQUEST, FactType.CHANGE_REQUEST}
REQUEST_STATUSES = {FactStatus.REQUESTED, FactStatus.PROPOSED, FactStatus.TENTATIVE}

COMMITMENT_CLAIM_TYPES = {
    FactType.SCOPE_ITEM,
    FactType.DELIVERABLE,
    FactType.ACCEPTANCE_CRITERIA,
    FactType.REQUIREMENT,
    FactType.UAT_TEST,
    FactType.SYSTEM_OR_INTEGRATION,
    FactType.DEPENDENCY,
    FactType.CHANGE_REQUEST,
}

RESPONSIBILITY_TYPES = {FactType.CLIENT_RESPONSIBILITY, FactType.TEAM_RESPONSIBILITY}
DATE_FACT_TYPES = {FactType.DATE, FactType.MILESTONE}

_VENDOR_MARKERS = ("auctor", "vendor")
_CLIENT_MARKERS = ("client", "northstar", "customer")
_CLIENT_OWNER_RE = re.compile(
    r"\b(?!auctor\b)(?!vendor\b)[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,2}"
    r"\s+(?:will|shall|must|owns?|is responsible|coordinates?|provides?|executes?)",
)


def _highest_authority_fact(facts: list[ProjectFact]) -> ProjectFact:
    return max(
        facts,
        key=lambda f: (f.source_authority_level, f.extraction_confidence),
    )


def _normalize_owner(owner: str | None) -> str | None:
    if not owner:
        return None
    lowered = owner.lower()
    if any(marker in lowered for marker in _VENDOR_MARKERS):
        return "vendor"
    if any(marker in lowered for marker in _CLIENT_MARKERS):
        return "client"
    if "joint" in lowered or "both" in lowered:
        return "joint"
    # Any other named organization is treated as the client party.
    if lowered.strip():
        return "client"
    return None


def _owner_from_text(text: str) -> str | None:
    """Infer the responsible party from a sentence when no owner attribute exists."""
    lowered = text.lower()
    has_vendor = any(marker in lowered for marker in _VENDOR_MARKERS)
    has_client = any(marker in lowered for marker in _CLIENT_MARKERS)
    if not has_client:
        client_match = _CLIENT_OWNER_RE.search(text)
        if client_match and "auctor" not in client_match.group(0).lower():
            has_client = True

    if has_vendor and not has_client:
        return "vendor"
    if has_client and not has_vendor:
        return "client"
    return None


def _resolve_owner(claim_or_fact_owner: str | None, text: str) -> str | None:
    return _normalize_owner(claim_or_fact_owner) or _owner_from_text(text)


def _claim_date_value(claim: TargetClaim):
    if claim.attributes and claim.attributes.date_value:
        return claim.attributes.date_value
    quote = claim.location.quote if claim.location else ""
    return extract_iso_date(claim.text) or extract_iso_date(quote)


def _fact_date_value(fact: ProjectFact):
    if fact.attributes and fact.attributes.date_value:
        return fact.attributes.date_value
    return extract_iso_date(fact.text) or extract_iso_date(fact.evidence.quote)


def _is_polarity_scope_conflict(claim: TargetClaim, fact: ProjectFact) -> bool:
    if claim.claim_type == FactType.OUT_OF_SCOPE_ITEM and claim.polarity == FactPolarity.NEGATIVE:
        return fact.fact_type == FactType.SCOPE_ITEM and fact.polarity == FactPolarity.POSITIVE
    return False


def _is_date_conflict(claim: TargetClaim, fact: ProjectFact) -> bool:
    if claim.claim_type not in DATE_FACT_TYPES or fact.fact_type not in DATE_FACT_TYPES:
        return False
    claim_date = _claim_date_value(claim)
    fact_date = _fact_date_value(fact)
    if claim_date is None or fact_date is None or claim_date == fact_date:
        return False
    claim_dt = claim.attributes.date_type if claim.attributes else None
    fact_dt = fact.attributes.date_type if fact.attributes else None
    if claim_dt is not None and fact_dt is not None and claim_dt != fact_dt:
        return False
    return subjects_share_meaningful_term(
        claim.normalized_subject, fact.normalized_subject
    ) or text_anchors_claim_to_fact(claim, fact)


def _find_date_conflicts(claim: TargetClaim, facts: list[ProjectFact]) -> list[ProjectFact]:
    if claim.claim_type not in DATE_FACT_TYPES:
        return []
    conflicts: list[ProjectFact] = []
    for fact in facts:
        if fact.fact_type not in DATE_FACT_TYPES:
            continue
        if _is_date_conflict(claim, fact):
            conflicts.append(fact)
    return conflicts


def _is_responsibility_conflict(claim: TargetClaim, fact: ProjectFact) -> bool:
    if claim.claim_type not in RESPONSIBILITY_TYPES:
        return False
    if fact.fact_type not in RESPONSIBILITY_TYPES:
        return False
    if not subjects_share_meaningful_term(
        claim.normalized_subject, fact.normalized_subject
    ) and not text_anchors_claim_to_fact(claim, fact):
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

    return claim.claim_type != fact.fact_type and fact.source_authority_level >= 4


def _find_responsibility_conflicts(
    claim: TargetClaim, facts: list[ProjectFact]
) -> list[ProjectFact]:
    if claim.claim_type not in RESPONSIBILITY_TYPES:
        return []
    return [fact for fact in facts if _is_responsibility_conflict(claim, fact)]


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
    "weekly check-in",
    "weekly check in",
    "check-ins",
    "check ins",
    "without a formal",
    "without formal",
)


def _is_change_control_weakening(claim: TargetClaim, fact: ProjectFact) -> bool:
    if claim.claim_type != FactType.CHANGE_REQUEST:
        return False
    if fact.fact_type != FactType.CHANGE_REQUEST:
        return False
    if fact.fact_status not in APPROVED_STATUSES:
        return False
    if not subjects_share_meaningful_term(
        claim.normalized_subject, fact.normalized_subject
    ) and not text_anchors_claim_to_fact(claim, fact):
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
    high_confidence = subjects_share_meaningful_term(
        claim.normalized_subject, fact.normalized_subject
    ) or text_anchors_claim_to_fact(claim, fact)
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
    title, message = unsupported_claim_copy(claim)
    return LintFinding(
        id=f"finding_{uuid4().hex}",
        project_id=context.project_id,
        target_document_id=claim.document_id,
        finding_type=LintFindingType.UNSUPPORTED_TARGET_CLAIM,
        severity=LintSeverity.MEDIUM,
        confidence=0.75,
        title=title,
        message=message,
        target_claim_id=claim.id,
        target_location=claim.location,
        target_quote=claim.location.quote,
        rule_id="grounding.unsupported_target_claim",
    )


def _find_authority_mismatch_facts(
    claim: TargetClaim, facts: list[ProjectFact], matches: list[ProjectFact]
) -> list[ProjectFact]:
    if claim.claim_type not in COMMITMENT_CLAIM_TYPES:
        return []

    candidate_facts = list(matches)
    for fact in facts:
        if fact in candidate_facts:
            continue
        if fact.fact_type not in REQUEST_FACT_TYPES and fact.fact_status not in REQUEST_STATUSES:
            continue
        if text_anchors_claim_to_fact(claim, fact):
            candidate_facts.append(fact)

    has_approving_support = any(
        f.fact_status in APPROVED_STATUSES
        or (f.fact_type not in REQUEST_FACT_TYPES and f.polarity != FactPolarity.NEGATIVE)
        for f in candidate_facts
    )
    only_requests = candidate_facts and all(
        f.fact_type in REQUEST_FACT_TYPES or f.fact_status in REQUEST_STATUSES
        for f in candidate_facts
    )
    if only_requests and not has_approving_support:
        return candidate_facts
    return []


def _classify_claim(context: LintContext, claim: TargetClaim) -> LintFinding | None:
    facts = context.project_facts
    matches = find_matching_facts(claim, facts)

    # Priority 1: explicit out-of-scope / exclusion contradiction.
    excluded = find_exclusion_facts(claim, facts)
    if excluded:
        fact = _highest_authority_fact(excluded)
        title, message = exclusion_contradiction_copy(claim, fact)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title=title,
            message=message,
            rule_id="contradiction.target_includes_excluded_item",
            severity_floor=LintSeverity.HIGH,
        )

    # Priority 2: opposite-polarity scope contradiction.
    polarity_conflicts = [f for f in matches if _is_polarity_scope_conflict(claim, f)]
    if polarity_conflicts:
        fact = _highest_authority_fact(polarity_conflicts)
        title, message = exclusion_contradiction_copy(claim, fact)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title=title,
            message=message,
            rule_id="contradiction.scope_opposite_polarity",
        )

    # Priority 3: date conflict.
    date_conflicts = _find_date_conflicts(claim, facts)
    if date_conflicts:
        fact = _highest_authority_fact(date_conflicts)
        title, message = date_conflict_copy(claim, fact)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title=title,
            message=message,
            rule_id="contradiction.date_conflict",
        )

    # Priority 4: responsibility / owner conflict.
    responsibility_conflicts = _find_responsibility_conflicts(claim, facts)
    if responsibility_conflicts:
        fact = _highest_authority_fact(responsibility_conflicts)
        title, message = responsibility_conflict_copy(claim, fact)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title=title,
            message=message,
            rule_id="contradiction.responsibility_conflict",
        )

    # Priority 5: change control weakened versus a signed/approved rule.
    change_control_conflicts = [f for f in matches if _is_change_control_weakening(claim, f)]
    if change_control_conflicts:
        fact = _highest_authority_fact(change_control_conflicts)
        title, message = change_control_copy(claim, fact)
        return _contradiction_finding(
            context=context,
            claim=claim,
            fact=fact,
            title=title,
            message=message,
            rule_id="contradiction.change_control_weakened",
            severity_floor=LintSeverity.HIGH,
        )

    # Priority 6: informal / requested item presented as approved scope.
    authority_facts = _find_authority_mismatch_facts(claim, facts, matches)
    if authority_facts:
        title, message = authority_mismatch_copy(claim, authority_facts)
        return LintFinding(
            id=f"finding_{uuid4().hex}",
            project_id=context.project_id,
            target_document_id=claim.document_id,
            finding_type=LintFindingType.STATUS_AUTHORITY_MISMATCH,
            severity=LintSeverity.HIGH,
            confidence=0.82,
            title=title,
            message=message,
            target_claim_id=claim.id,
            target_location=claim.location,
            related_fact_ids=[f.id for f in authority_facts],
            related_source_profile_ids=list({f.source_profile_id for f in authority_facts}),
            target_quote=claim.location.quote,
            reference_quotes=[f.evidence.quote for f in authority_facts],
            rule_id="authority.request_presented_as_scope",
        )

    if not matches:
        if not has_reference_coverage_for_claim(claim, context.source_profiles):
            return None
        return _unsupported_finding(context, claim)

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
