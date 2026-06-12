"""Document content and eligibility configuration."""

from backend.app.schemas.enums import DocType, FactCategory, SourceStatus

DEFAULT_EXPECTED_CONTENT_BY_DOC_TYPE: dict[DocType, list[FactCategory]] = {
    DocType.SIGNED_SOW: [
        FactCategory.SCOPE,
        FactCategory.OUT_OF_SCOPE,
        FactCategory.DELIVERABLES,
        FactCategory.DATES,
        FactCategory.ASSUMPTIONS,
        FactCategory.DEPENDENCIES,
        FactCategory.RESPONSIBILITIES,
        FactCategory.ACCEPTANCE_CRITERIA,
        FactCategory.CHANGE_REQUESTS,
        FactCategory.SYSTEMS,
    ],
    DocType.DRAFT_SOW: [
        FactCategory.SCOPE,
        FactCategory.OUT_OF_SCOPE,
        FactCategory.DELIVERABLES,
        FactCategory.DATES,
        FactCategory.ASSUMPTIONS,
        FactCategory.DEPENDENCIES,
        FactCategory.RESPONSIBILITIES,
        FactCategory.ACCEPTANCE_CRITERIA,
        FactCategory.CHANGE_REQUESTS,
        FactCategory.SYSTEMS,
    ],
    DocType.REQUIREMENTS_DOC: [
        FactCategory.REQUIREMENTS,
        FactCategory.ACCEPTANCE_CRITERIA,
        FactCategory.STAKEHOLDERS,
        FactCategory.SYSTEMS,
        FactCategory.DEPENDENCIES,
        FactCategory.OPEN_QUESTIONS,
    ],
    DocType.UAT_PLAN: [
        FactCategory.UAT_TESTS,
        FactCategory.ACCEPTANCE_CRITERIA,
        FactCategory.REQUIREMENTS,
        FactCategory.RESPONSIBILITIES,
        FactCategory.DATES,
        FactCategory.SYSTEMS,
    ],
    DocType.MEETING_TRANSCRIPT: [
        FactCategory.CLIENT_REQUESTS,
        FactCategory.DECISIONS,
        FactCategory.RISKS,
        FactCategory.DATES,
        FactCategory.OPEN_QUESTIONS,
        FactCategory.RESPONSIBILITIES,
        FactCategory.REQUIREMENTS,
        FactCategory.SYSTEMS,
        FactCategory.STAKEHOLDERS,
        FactCategory.STATUS_UPDATES,
    ],
    DocType.CLIENT_EMAIL: [
        FactCategory.CLIENT_REQUESTS,
        FactCategory.DECISIONS,
        FactCategory.DATES,
        FactCategory.OPEN_QUESTIONS,
        FactCategory.REQUIREMENTS,
        FactCategory.RISKS,
        FactCategory.RESPONSIBILITIES,
        FactCategory.SYSTEMS,
        FactCategory.CHANGE_REQUESTS,
    ],
    DocType.PROJECT_PLAN: [
        FactCategory.DATES,
        FactCategory.DELIVERABLES,
        FactCategory.RESPONSIBILITIES,
        FactCategory.DEPENDENCIES,
        FactCategory.RISKS,
        FactCategory.STATUS_UPDATES,
    ],
    DocType.CHANGE_ORDER: [
        FactCategory.CHANGE_REQUESTS,
        FactCategory.SCOPE,
        FactCategory.OUT_OF_SCOPE,
        FactCategory.DELIVERABLES,
        FactCategory.DATES,
        FactCategory.RESPONSIBILITIES,
        FactCategory.ASSUMPTIONS,
        FactCategory.DEPENDENCIES,
    ],
    DocType.STATUS_REPORT: [
        FactCategory.STATUS_UPDATES,
        FactCategory.RISKS,
        FactCategory.DATES,
        FactCategory.RESPONSIBILITIES,
        FactCategory.OPEN_QUESTIONS,
        FactCategory.DECISIONS,
        FactCategory.DELIVERABLES,
    ],
    DocType.UNKNOWN: [],
}

TARGET_ELIGIBLE_DOC_TYPES: set[DocType] = {
    DocType.DRAFT_SOW,
    DocType.REQUIREMENTS_DOC,
    DocType.UAT_PLAN,
    DocType.PROJECT_PLAN,
    DocType.CHANGE_ORDER,
    DocType.STATUS_REPORT,
}

REFERENCE_ONLY_DOC_TYPES: set[DocType] = {
    DocType.SIGNED_SOW,
    DocType.MEETING_TRANSCRIPT,
    DocType.CLIENT_EMAIL,
}

FACT_CATEGORY_KEYWORDS: dict[FactCategory, list[str]] = {
    FactCategory.SCOPE: ["scope", "in scope", "included"],
    FactCategory.OUT_OF_SCOPE: ["out of scope", "excluded", "not included"],
    FactCategory.REQUIREMENTS: ["requirement", "shall", "must"],
    FactCategory.ACCEPTANCE_CRITERIA: ["acceptance", "criteria", "expected result"],
    FactCategory.UAT_TESTS: ["uat", "test case", "test scenario"],
    FactCategory.DELIVERABLES: ["deliverable", "deliverables"],
    FactCategory.DATES: ["date", "go-live", "kickoff", "deadline"],
    FactCategory.ASSUMPTIONS: ["assumption", "assume"],
    FactCategory.DEPENDENCIES: ["dependency", "depends on"],
    FactCategory.RESPONSIBILITIES: ["responsible", "responsibility", "owner"],
    FactCategory.SYSTEMS: ["system", "integration", "salesforce", "netsuite"],
    FactCategory.CHANGE_REQUESTS: ["change order", "change request"],
    FactCategory.CLIENT_REQUESTS: ["request", "please", "can we"],
    FactCategory.DECISIONS: ["decision", "approved", "agreed"],
    FactCategory.RISKS: ["risk", "blocker"],
    FactCategory.OPEN_QUESTIONS: ["question", "tbd", "clarify"],
    FactCategory.STAKEHOLDERS: ["stakeholder", "sponsor"],
    FactCategory.STATUS_UPDATES: ["status", "completed", "progress"],
}


def is_target_eligible_doc_type(
    doc_type: DocType,
    status: SourceStatus | None = None,
) -> bool:
    if doc_type == DocType.UNKNOWN:
        return False

    if doc_type == DocType.CHANGE_ORDER:
        return status in {SourceStatus.DRAFT, SourceStatus.UNKNOWN, None}

    return doc_type in TARGET_ELIGIBLE_DOC_TYPES


def get_expected_content(doc_type: DocType) -> list[FactCategory]:
    return list(DEFAULT_EXPECTED_CONTENT_BY_DOC_TYPE.get(doc_type, []))
