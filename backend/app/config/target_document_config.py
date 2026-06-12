"""Target document parsing configuration by document type."""

from pydantic import BaseModel

from backend.app.schemas.enums import DocType, FactCategory, FactType

MIN_TARGET_CLAIM_CONFIDENCE = 0.5


class TargetDocumentConfig(BaseModel):
    expected_content: list[FactCategory]
    target_claim_types: list[FactType]
    target_rubric_id: str
    parsing_guidance: str
    rubric_guidance: str


TARGET_DOCUMENT_CONFIG_BY_DOC_TYPE: dict[DocType, TargetDocumentConfig] = {
    DocType.DRAFT_SOW: TargetDocumentConfig(
        expected_content=[
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
        target_claim_types=[
            FactType.SCOPE_ITEM,
            FactType.OUT_OF_SCOPE_ITEM,
            FactType.DELIVERABLE,
            FactType.DATE,
            FactType.ASSUMPTION,
            FactType.DEPENDENCY,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.TEAM_RESPONSIBILITY,
            FactType.ACCEPTANCE_CRITERIA,
            FactType.SYSTEM_OR_INTEGRATION,
            FactType.CHANGE_REQUEST,
        ],
        target_rubric_id="draft_sow_v0",
        parsing_guidance=(
            "Parse the draft SOW into checkable claims about scope, exclusions, "
            "deliverables, dates, assumptions, dependencies, responsibilities, "
            "acceptance criteria, systems, and change-order terms."
        ),
        rubric_guidance=(
            "A draft SOW should clearly distinguish in-scope and out-of-scope work, "
            "list deliverables, define assumptions, assign responsibilities, specify "
            "dates, and describe change-order handling."
        ),
    ),
    DocType.REQUIREMENTS_DOC: TargetDocumentConfig(
        expected_content=[
            FactCategory.REQUIREMENTS,
            FactCategory.ACCEPTANCE_CRITERIA,
            FactCategory.STAKEHOLDERS,
            FactCategory.SYSTEMS,
            FactCategory.DEPENDENCIES,
            FactCategory.OPEN_QUESTIONS,
        ],
        target_claim_types=[
            FactType.REQUIREMENT,
            FactType.ACCEPTANCE_CRITERIA,
            FactType.DEPENDENCY,
            FactType.STAKEHOLDER,
            FactType.SYSTEM_OR_INTEGRATION,
            FactType.OPEN_QUESTION,
            FactType.RISK,
        ],
        target_rubric_id="requirements_doc_v0",
        parsing_guidance=(
            "Parse the requirements document into checkable functional requirements, "
            "non-functional requirements, acceptance criteria, dependencies, systems, "
            "stakeholders, risks, and open questions."
        ),
        rubric_guidance=(
            "A requirements document should contain clear, testable requirements, "
            "acceptance criteria where possible, relevant stakeholders/systems, "
            "dependencies, and unresolved questions."
        ),
    ),
    DocType.UAT_PLAN: TargetDocumentConfig(
        expected_content=[
            FactCategory.UAT_TESTS,
            FactCategory.ACCEPTANCE_CRITERIA,
            FactCategory.REQUIREMENTS,
            FactCategory.RESPONSIBILITIES,
            FactCategory.DATES,
            FactCategory.SYSTEMS,
        ],
        target_claim_types=[
            FactType.UAT_TEST,
            FactType.ACCEPTANCE_CRITERIA,
            FactType.REQUIREMENT,
            FactType.DATE,
            FactType.TEAM_RESPONSIBILITY,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.SYSTEM_OR_INTEGRATION,
        ],
        target_rubric_id="uat_plan_v0",
        parsing_guidance=(
            "Parse the UAT plan into checkable UAT tests, expected results, linked "
            "requirements, owners, dates, systems, and acceptance criteria."
        ),
        rubric_guidance=(
            "A UAT plan should contain testable scenarios, expected results, linked "
            "requirements where possible, owners, systems/environments, and relevant dates."
        ),
    ),
    DocType.PROJECT_PLAN: TargetDocumentConfig(
        expected_content=[
            FactCategory.DATES,
            FactCategory.DELIVERABLES,
            FactCategory.RESPONSIBILITIES,
            FactCategory.DEPENDENCIES,
            FactCategory.RISKS,
            FactCategory.STATUS_UPDATES,
        ],
        target_claim_types=[
            FactType.DATE,
            FactType.MILESTONE,
            FactType.DELIVERABLE,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.TEAM_RESPONSIBILITY,
            FactType.DEPENDENCY,
            FactType.RISK,
            FactType.STATUS_UPDATE,
        ],
        target_rubric_id="project_plan_v0",
        parsing_guidance=(
            "Parse the project plan into checkable milestones, dates, owners, "
            "deliverables, dependencies, risks, and status/planning updates."
        ),
        rubric_guidance=(
            "A project plan should define milestones, dates, owners, dependencies, "
            "risks, deliverables, and the current/projected status of major workstreams."
        ),
    ),
    DocType.CHANGE_ORDER: TargetDocumentConfig(
        expected_content=[
            FactCategory.CHANGE_REQUESTS,
            FactCategory.SCOPE,
            FactCategory.OUT_OF_SCOPE,
            FactCategory.DELIVERABLES,
            FactCategory.DATES,
            FactCategory.RESPONSIBILITIES,
            FactCategory.ASSUMPTIONS,
            FactCategory.DEPENDENCIES,
        ],
        target_claim_types=[
            FactType.CHANGE_REQUEST,
            FactType.SCOPE_ITEM,
            FactType.OUT_OF_SCOPE_ITEM,
            FactType.DELIVERABLE,
            FactType.DATE,
            FactType.ASSUMPTION,
            FactType.DEPENDENCY,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.TEAM_RESPONSIBILITY,
            FactType.DECISION,
        ],
        target_rubric_id="change_order_v0",
        parsing_guidance=(
            "Parse the change order into checkable claims about changed scope, "
            "added/removed deliverables, date impacts, assumptions, dependencies, "
            "responsibility changes, and approval/decision language."
        ),
        rubric_guidance=(
            "A change order should clearly state what is changing, why it is changing, "
            "the impact on scope/deliverables/dates/responsibilities, and whether it "
            "has been approved or remains proposed."
        ),
    ),
    DocType.STATUS_REPORT: TargetDocumentConfig(
        expected_content=[
            FactCategory.STATUS_UPDATES,
            FactCategory.RISKS,
            FactCategory.DATES,
            FactCategory.RESPONSIBILITIES,
            FactCategory.OPEN_QUESTIONS,
            FactCategory.DECISIONS,
            FactCategory.DELIVERABLES,
        ],
        target_claim_types=[
            FactType.STATUS_UPDATE,
            FactType.RISK,
            FactType.DATE,
            FactType.TEAM_RESPONSIBILITY,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.OPEN_QUESTION,
            FactType.DECISION,
            FactType.DELIVERABLE,
            FactType.MILESTONE,
        ],
        target_rubric_id="status_report_v0",
        parsing_guidance=(
            "Parse the status report into checkable status updates, risks, blockers, "
            "dates, responsibilities, open questions, decisions, deliverables, and milestones."
        ),
        rubric_guidance=(
            "A status report should clearly distinguish completed work, current work, "
            "upcoming work, risks/blockers, owner responsibilities, timeline updates, "
            "open questions, and decisions."
        ),
    ),
}
