"""Lint engine matching helpers."""

from backend.app.schemas.enums import FactCategory, FactType
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
        FactType.CHANGE_REQUEST,
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
    "seamless",
    "robust",
    "user-friendly",
    "as needed",
    "etc.",
    "appropriate",
    "reasonable",
    "optimize",
    "improve",
}


def subjects_match(a: str, b: str) -> bool:
    return a == b


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


def find_matching_facts(claim: TargetClaim, facts: list[ProjectFact]) -> list[ProjectFact]:
    matches: list[ProjectFact] = []
    for fact in facts:
        if not subjects_match(claim.normalized_subject, fact.normalized_subject):
            continue
        if not compatible_fact_types(claim.claim_type, fact.fact_type):
            continue
        matches.append(fact)
    return matches


def contains_vague_language(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in VAGUE_TERMS)


def uat_test_has_expected_result(claim: TargetClaim) -> bool:
    text = claim.text.lower()
    return (
        "expected result" in text
        or "should" in text
        or "verify" in text
        or bool(claim.attributes and claim.attributes.linked_requirement_ids)
    )
