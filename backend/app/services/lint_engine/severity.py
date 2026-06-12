"""Lint severity helpers."""

from backend.app.schemas.enums import DocType, FactCategory, LintSeverity

SEVERITY_RANK = {
    LintSeverity.CRITICAL: 4,
    LintSeverity.HIGH: 3,
    LintSeverity.MEDIUM: 2,
    LintSeverity.LOW: 1,
}

HIGH_IMPORTANCE_MISSING = {
    (DocType.DRAFT_SOW, FactCategory.SCOPE),
    (DocType.DRAFT_SOW, FactCategory.OUT_OF_SCOPE),
    (DocType.DRAFT_SOW, FactCategory.RESPONSIBILITIES),
    (DocType.UAT_PLAN, FactCategory.UAT_TESTS),
    (DocType.UAT_PLAN, FactCategory.ACCEPTANCE_CRITERIA),
    (DocType.REQUIREMENTS_DOC, FactCategory.REQUIREMENTS),
    (DocType.REQUIREMENTS_DOC, FactCategory.ACCEPTANCE_CRITERIA),
    (DocType.CHANGE_ORDER, FactCategory.CHANGE_REQUESTS),
}


def severity_for_missing_content(doc_type: DocType, category: FactCategory) -> LintSeverity:
    if (doc_type, category) in HIGH_IMPORTANCE_MISSING:
        return LintSeverity.HIGH
    return LintSeverity.MEDIUM


def severity_for_authority_contradiction(authority_level: int) -> LintSeverity:
    if authority_level >= 5:
        return LintSeverity.CRITICAL
    if authority_level == 4:
        return LintSeverity.HIGH
    if authority_level == 3:
        return LintSeverity.MEDIUM
    return LintSeverity.LOW
