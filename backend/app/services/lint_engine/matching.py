"""Lint engine matching helpers."""

import re

from backend.app.config.party_config import (
    CLIENT_MARKERS,
    CLIENT_NAME_TOKENS,
    VENDOR_MARKERS,
    VENDOR_NAME_TOKENS,
)
from backend.app.schemas.enums import FactCategory, FactPolarity, FactType
from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.source_profile import SourceProfile
from backend.app.schemas.target_document import TargetClaim

COMPATIBLE_REFERENCE_FACT_TYPES_BY_CLAIM_TYPE: dict[FactType, set[FactType]] = {
    FactType.SCOPE_ITEM: {
        FactType.SCOPE_ITEM,
        FactType.OUT_OF_SCOPE_ITEM,
        FactType.CLIENT_REQUEST,
        FactType.CHANGE_REQUEST,
        FactType.DECISION,
    },
    FactType.OUT_OF_SCOPE_ITEM: {
        FactType.OUT_OF_SCOPE_ITEM,
        FactType.SCOPE_ITEM,
        FactType.DECISION,
        FactType.CHANGE_REQUEST,
    },
    FactType.REQUIREMENT: {
        FactType.REQUIREMENT,
        FactType.ACCEPTANCE_CRITERIA,
        FactType.CLIENT_REQUEST,
        FactType.DECISION,
        FactType.OPEN_QUESTION,
        FactType.OUT_OF_SCOPE_ITEM,
        FactType.SCOPE_ITEM,
        FactType.SYSTEM_OR_INTEGRATION,
    },
    FactType.ACCEPTANCE_CRITERIA: {
        FactType.ACCEPTANCE_CRITERIA,
        FactType.REQUIREMENT,
        FactType.UAT_TEST,
    },
    FactType.UAT_TEST: {
        FactType.UAT_TEST,
        FactType.REQUIREMENT,
        FactType.ACCEPTANCE_CRITERIA,
        FactType.OUT_OF_SCOPE_ITEM,
    },
    FactType.DATE: {
        FactType.DATE,
        FactType.MILESTONE,
        FactType.DECISION,
        FactType.STATUS_UPDATE,
    },
    FactType.DELIVERABLE: {
        FactType.DELIVERABLE,
        FactType.SCOPE_ITEM,
        FactType.OUT_OF_SCOPE_ITEM,
        FactType.CHANGE_REQUEST,
        FactType.DECISION,
    },
    FactType.DEPENDENCY: {
        FactType.DEPENDENCY,
        FactType.ASSUMPTION,
        FactType.OUT_OF_SCOPE_ITEM,
        FactType.SYSTEM_OR_INTEGRATION,
        FactType.CLIENT_RESPONSIBILITY,
        FactType.DECISION,
    },
    FactType.ASSUMPTION: {
        FactType.ASSUMPTION,
        FactType.DEPENDENCY,
        FactType.OUT_OF_SCOPE_ITEM,
        FactType.SCOPE_ITEM,
        FactType.SYSTEM_OR_INTEGRATION,
        FactType.DECISION,
    },
    FactType.SYSTEM_OR_INTEGRATION: {
        FactType.SYSTEM_OR_INTEGRATION,
        FactType.SCOPE_ITEM,
        FactType.OUT_OF_SCOPE_ITEM,
        FactType.DEPENDENCY,
        FactType.DECISION,
    },
    FactType.CLIENT_RESPONSIBILITY: {
        FactType.CLIENT_RESPONSIBILITY,
        FactType.TEAM_RESPONSIBILITY,
        FactType.DEPENDENCY,
        FactType.DECISION,
    },
    FactType.TEAM_RESPONSIBILITY: {
        FactType.TEAM_RESPONSIBILITY,
        FactType.CLIENT_RESPONSIBILITY,
        FactType.DEPENDENCY,
        FactType.DECISION,
    },
    FactType.CHANGE_REQUEST: {
        FactType.CHANGE_REQUEST,
        FactType.CLIENT_REQUEST,
        FactType.DECISION,
        FactType.SCOPE_ITEM,
        FactType.OUT_OF_SCOPE_ITEM,
    },
}

REQUIRED_CATEGORIES_BY_CLAIM_TYPE: dict[FactType, set[FactCategory]] = {
    FactType.SCOPE_ITEM: {FactCategory.SCOPE, FactCategory.OUT_OF_SCOPE},
    FactType.OUT_OF_SCOPE_ITEM: {FactCategory.SCOPE, FactCategory.OUT_OF_SCOPE},
    FactType.REQUIREMENT: {FactCategory.REQUIREMENTS},
    FactType.UAT_TEST: {FactCategory.UAT_TESTS, FactCategory.REQUIREMENTS},
    FactType.DATE: {FactCategory.DATES},
    FactType.DELIVERABLE: {FactCategory.DELIVERABLES, FactCategory.SCOPE},
    FactType.CLIENT_RESPONSIBILITY: {FactCategory.RESPONSIBILITIES},
    FactType.TEAM_RESPONSIBILITY: {FactCategory.RESPONSIBILITIES},
    FactType.CHANGE_REQUEST: {FactCategory.CHANGE_REQUESTS},
}

VAGUE_TERMS = {
    "fast",
    "easy",
    "easily",
    "quickly",
    "seamless",
    "robust",
    "user-friendly",
    "user friendly",
    "intuitive",
    "as needed",
    "etc.",
    "appropriate",
    "reasonable",
    "optimize",
    "improve",
    "straightforward",
    "work properly",
    "work efficiently",
    "efficiently",
    "simple and seamless",
    "easier to manage",
}

# Generic tokens that do not help disambiguate one subject from another.
# Removing them prevents over-matching on boilerplate words while keeping the
# domain-specific anchor tokens (e.g. "netsuite", "portal", "uat") intact. Party
# names (vendor/client) are pulled from party_config so they generalize across
# engagements rather than being hardcoded here.
SUBJECT_STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "for",
    "to",
    "and",
    "or",
    "in",
    "on",
    "with",
    "by",
    "project",
    "release",
    "salesforce",
    "system",
    "systems",
    "new",
    "item",
    "items",
    "general",
    "support",
    *VENDOR_NAME_TOKENS,
    *CLIENT_NAME_TOKENS,
}

# Minimum overlap-coefficient (|A ∩ B| / min(|A|, |B|)) required to treat two
# normalized subjects as referring to the same thing.
SUBJECT_MATCH_THRESHOLD = 0.5

# Tokens that are too generic to anchor a *contradiction* or *exclusion* match.
# Two subjects sharing only these words (e.g. "integration", "access") describe
# different things and must not be treated as the same excluded capability or the
# same responsibility. They remain usable for loose ``subjects_match`` grouping,
# but a contradiction/exclusion additionally requires a shared *meaningful* term.
GENERIC_MATCH_TERMS = {
    "integration",
    "integrations",
    "access",
    "testing",
    "test",
    "tests",
    "support",
    "system",
    "systems",
    "workflow",
    "workflows",
    "data",
    "object",
    "objects",
    "configuration",
    "management",
    "service",
    "services",
}


def subject_tokens(normalized_subject: str) -> set[str]:
    tokens = {
        token
        for token in re.split(r"[^a-z0-9]+", normalized_subject.lower())
        if token
    }
    significant = {token for token in tokens if token not in SUBJECT_STOPWORDS}
    # Fall back to the raw tokens if stopword removal emptied the set so that very
    # short subjects (e.g. "systems") can still match an identical counterpart.
    return significant or tokens


def subjects_match(a: str, b: str) -> bool:
    """Return True when two normalized subjects plausibly describe the same thing.

    Subjects are produced by independent LLM extraction passes for the target and
    the reference documents, so exact-string equality misses obvious matches such
    as ``netsuite_billing_sync`` vs ``netsuite_billing_integration``. We therefore
    compare significant-token sets using an overlap coefficient plus subset
    detection.
    """
    if a == b:
        return True

    tokens_a = subject_tokens(a)
    tokens_b = subject_tokens(b)
    if not tokens_a or not tokens_b:
        return False

    shared = tokens_a & tokens_b
    if not shared:
        return False

    # Subset relationship (e.g. "customer_portal" ⊂ "customer_portal_quote_acceptance").
    if shared == tokens_a or shared == tokens_b:
        return True

    overlap_coefficient = len(shared) / min(len(tokens_a), len(tokens_b))
    return overlap_coefficient >= SUBJECT_MATCH_THRESHOLD


def meaningful_shared_tokens(a: str, b: str) -> set[str]:
    """Significant tokens shared by two subjects, excluding generic boilerplate.

    A bare overlap on words like ``integration`` or ``access`` is not enough to
    conclude two subjects describe the same excluded capability or responsibility.
    This returns only the domain-specific anchor tokens they share (e.g.
    ``netsuite``, ``billing``, ``portal``, ``uat``).
    """
    shared = subject_tokens(a) & subject_tokens(b)
    return shared - GENERIC_MATCH_TERMS


def subjects_share_meaningful_term(a: str, b: str) -> bool:
    """True when two subjects share at least one non-generic anchor token."""
    return bool(meaningful_shared_tokens(a, b))


def compatible_fact_types(claim_type: FactType, fact_type: FactType) -> bool:
    allowed = COMPATIBLE_REFERENCE_FACT_TYPES_BY_CLAIM_TYPE.get(claim_type)
    if allowed is None:
        return claim_type == fact_type
    return fact_type in allowed


def has_reference_coverage_for_claim(
    claim: TargetClaim,
    source_profiles: list[SourceProfile],
) -> bool:
    required_categories = REQUIRED_CATEGORIES_BY_CLAIM_TYPE.get(claim.claim_type)
    if not required_categories:
        return True

    for profile in source_profiles:
        if any(category in profile.observed_content for category in required_categories):
            return True
    return False


def text_anchors_claim_to_fact(claim: TargetClaim, fact: ProjectFact) -> bool:
    """True when claim text mentions domain terms from a reference fact subject.

    Only compares against the fact's subject tokens — not every word in the
    evidence quote — to avoid spurious matches (e.g. a contractor-onboarding
    exclusion matching unrelated onboarding requirements).
    """
    quote = claim.location.quote if claim.location else ""
    claim_corpus = " ".join(
        [
            claim.text,
            claim.subject,
            claim.normalized_subject.replace("_", " "),
            quote,
        ]
    ).lower()

    fact_tokens = subject_tokens(fact.normalized_subject) | subject_tokens(fact.subject)
    meaningful = fact_tokens - GENERIC_MATCH_TERMS - SUBJECT_STOPWORDS
    if not meaningful:
        return False

    hits = sum(1 for token in meaningful if token in claim_corpus)
    required = 1 if len(meaningful) == 1 else min(2, len(meaningful))
    return hits >= required


def exclusion_anchors_claim(claim: TargetClaim, fact: ProjectFact) -> bool:
    """Stricter anchor for out-of-scope exclusions than general fact matching."""
    if subjects_share_meaningful_term(claim.normalized_subject, fact.normalized_subject):
        return True
    return text_anchors_claim_to_fact(claim, fact)


def find_subject_or_text_matches(
    claim: TargetClaim,
    facts: list[ProjectFact],
) -> list[ProjectFact]:
    """Match facts by normalized subject or by text-anchor overlap."""
    matches: list[ProjectFact] = []
    for fact in facts:
        if not compatible_fact_types(claim.claim_type, fact.fact_type):
            continue
        if subjects_match(claim.normalized_subject, fact.normalized_subject):
            matches.append(fact)
        elif text_anchors_claim_to_fact(claim, fact):
            matches.append(fact)
    return matches


def find_matching_facts(claim: TargetClaim, facts: list[ProjectFact]) -> list[ProjectFact]:
    return find_subject_or_text_matches(claim, facts)


def find_exclusion_facts(claim: TargetClaim, facts: list[ProjectFact]) -> list[ProjectFact]:
    """Find reference facts that exclude work the target claim commits to."""
    if claim.polarity == FactPolarity.NEGATIVE:
        return []
    if claim.claim_type not in {
        FactType.SCOPE_ITEM,
        FactType.DELIVERABLE,
        FactType.ACCEPTANCE_CRITERIA,
        FactType.REQUIREMENT,
        FactType.UAT_TEST,
        FactType.SYSTEM_OR_INTEGRATION,
        FactType.DEPENDENCY,
        FactType.CHANGE_REQUEST,
    }:
        return []

    excluded: list[ProjectFact] = []
    for fact in facts:
        if fact.fact_type != FactType.OUT_OF_SCOPE_ITEM:
            continue
        if subjects_share_meaningful_term(claim.normalized_subject, fact.normalized_subject):
            excluded.append(fact)
        elif exclusion_anchors_claim(claim, fact):
            excluded.append(fact)
    return excluded


def contains_vague_language(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in VAGUE_TERMS)


# Owner names / named roles whose presence in a sentence means the owner is
# explicit, so a "missing owner" finding would be a false positive. The party
# names/roles come from party_config so this generalizes across engagements.
EXPLICIT_OWNER_TERMS = {
    "project team",
    "sponsor",
    "engagement manager",
    "administrator",
    "admin",
    "manager",
    "lead",
    "owner",
    "sales operations",
    "finance",
    "stakeholder",
    *VENDOR_MARKERS,
    *CLIENT_MARKERS,
}

# Verbs indicating an actionable task (something a party is expected to do).
# Kept deliberately unambiguous to avoid matching adjectives (e.g. "complete").
ACTION_VERBS = {
    "will",
    "shall",
    "must",
    "provide",
    "deliver",
    "configure",
    "execute",
    "install",
    "identify",
    "review",
    "approve",
    "prepare",
    "conduct",
    "manage",
    "perform",
    "assign",
    "verify",
    "participate",
}


def mentions_explicit_owner(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in EXPLICIT_OWNER_TERMS)


def is_actionable_task(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(verb)}\b", lowered) for verb in ACTION_VERBS)


def uat_covers_requirement(
    requirement_subject: str,
    requirement_id: str | None,
    requirement_text: str,
    uat_claims: list[TargetClaim],
) -> bool:
    for uat in uat_claims:
        linked = uat.attributes.linked_requirement_ids if uat.attributes else None
        if requirement_id and linked and requirement_id.upper() in {
            item.upper() for item in linked
        }:
            return True
        uat_req_id = uat.attributes.requirement_id if uat.attributes else None
        if requirement_id and uat_req_id and requirement_id.upper() == uat_req_id.upper():
            return True
        if requirement_id and requirement_id.upper() in uat.text.upper():
            return True
        if subjects_match(requirement_subject, uat.normalized_subject):
            return True
        if requirement_id and requirement_id.upper() in uat.normalized_subject.upper():
            return True
    return False


def uat_test_has_expected_result(claim: TargetClaim) -> bool:
    text = claim.text.lower()
    return (
        "expected result" in text
        or "should" in text
        or "verify" in text
        or bool(claim.attributes and claim.attributes.linked_requirement_ids)
    )
