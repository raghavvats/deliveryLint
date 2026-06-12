"""Fact extraction configuration by document type."""

from pydantic import BaseModel

from backend.app.schemas.enums import DocType, FactType

MIN_EXTRACTION_CONFIDENCE = 0.5


class FactExtractionConfig(BaseModel):
    target_fact_types: list[FactType]
    extraction_guidance: str
    status_guidance: str


FACT_EXTRACTION_CONFIG_BY_DOC_TYPE: dict[DocType, FactExtractionConfig] = {
    DocType.SIGNED_SOW: FactExtractionConfig(
        target_fact_types=[
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
        extraction_guidance=(
            "Extract official contractual scope, exclusions, deliverables, dates, "
            "assumptions, dependencies, responsibilities, acceptance/signoff terms, "
            "and systems/integrations."
        ),
        status_guidance=(
            "Facts from a signed SOW should generally be treated as signed or "
            "confirmed unless the text explicitly says otherwise."
        ),
    ),
    DocType.DRAFT_SOW: FactExtractionConfig(
        target_fact_types=[
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
        extraction_guidance=(
            "Extract proposed scope, exclusions, deliverables, dates, assumptions, "
            "dependencies, responsibilities, acceptance/signoff terms, and "
            "systems/integrations."
        ),
        status_guidance=(
            "Facts from a draft SOW should generally be treated as proposed unless "
            "the text clearly references already-approved or signed terms."
        ),
    ),
    DocType.REQUIREMENTS_DOC: FactExtractionConfig(
        target_fact_types=[
            FactType.REQUIREMENT,
            FactType.ACCEPTANCE_CRITERIA,
            FactType.DEPENDENCY,
            FactType.STAKEHOLDER,
            FactType.SYSTEM_OR_INTEGRATION,
            FactType.OPEN_QUESTION,
            FactType.RISK,
        ],
        extraction_guidance=(
            "Extract functional requirements, non-functional requirements, acceptance "
            "criteria, business goals, actors/users, systems involved, priorities, "
            "dependencies, stakeholders, risks, and open questions."
        ),
        status_guidance=(
            "Requirements may be approved, proposed, or unknown depending on the "
            "document status and wording. Preserve requirement IDs where available."
        ),
    ),
    DocType.UAT_PLAN: FactExtractionConfig(
        target_fact_types=[
            FactType.UAT_TEST,
            FactType.ACCEPTANCE_CRITERIA,
            FactType.REQUIREMENT,
            FactType.DATE,
            FactType.TEAM_RESPONSIBILITY,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.SYSTEM_OR_INTEGRATION,
        ],
        extraction_guidance=(
            "Extract UAT test cases, test steps, expected results, linked requirements, "
            "test owners, pass/fail criteria, dates, and systems."
        ),
        status_guidance=(
            "UAT facts are generally planned or approved depending on document status. "
            "Preserve test IDs and linked requirement IDs where available."
        ),
    ),
    DocType.MEETING_TRANSCRIPT: FactExtractionConfig(
        target_fact_types=[
            FactType.CLIENT_REQUEST,
            FactType.DECISION,
            FactType.RISK,
            FactType.DATE,
            FactType.OPEN_QUESTION,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.TEAM_RESPONSIBILITY,
            FactType.REQUIREMENT,
            FactType.SYSTEM_OR_INTEGRATION,
            FactType.STAKEHOLDER,
            FactType.STATUS_UPDATE,
            FactType.CHANGE_REQUEST,
        ],
        extraction_guidance=(
            "Extract client requests, confirmed decisions, risks, date changes, open "
            "questions, responsibilities, requirements, systems/integrations, "
            "stakeholders, status updates, and change requests."
        ),
        status_guidance=(
            "Be careful to distinguish confirmed decisions from tentative discussion, "
            "brainstorming, questions, or requests. Do not treat tentative language "
            "as approved scope."
        ),
    ),
    DocType.CLIENT_EMAIL: FactExtractionConfig(
        target_fact_types=[
            FactType.CLIENT_REQUEST,
            FactType.DECISION,
            FactType.DATE,
            FactType.OPEN_QUESTION,
            FactType.REQUIREMENT,
            FactType.RISK,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.SYSTEM_OR_INTEGRATION,
            FactType.CHANGE_REQUEST,
        ],
        extraction_guidance=(
            "Extract client asks, approvals, clarifications, objections, date changes, "
            "scope asks, requirements, risks, responsibility confirmations, and "
            "change requests."
        ),
        status_guidance=(
            "Distinguish requested, approved, rejected, tentative, and open-question "
            "language. Do not treat a client question as approved scope."
        ),
    ),
    DocType.PROJECT_PLAN: FactExtractionConfig(
        target_fact_types=[
            FactType.DATE,
            FactType.MILESTONE,
            FactType.DELIVERABLE,
            FactType.CLIENT_RESPONSIBILITY,
            FactType.TEAM_RESPONSIBILITY,
            FactType.DEPENDENCY,
            FactType.RISK,
            FactType.STATUS_UPDATE,
        ],
        extraction_guidance=(
            "Extract kickoff dates, UAT dates, go-live dates, milestones, owners, "
            "dependencies, risks, deliverables, and status updates."
        ),
        status_guidance=(
            "Project plan facts are operational planning facts. Treat them as approved "
            "only if the document/profile indicates approval."
        ),
    ),
    DocType.CHANGE_ORDER: FactExtractionConfig(
        target_fact_types=[
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
        extraction_guidance=(
            "Extract changed scope, added or removed deliverables, timeline impact, "
            "responsibility changes, assumptions, dependencies, and approval status."
        ),
        status_guidance=(
            "If the change order is signed or approved, facts may be signed or "
            "approved. If it is draft, treat facts as proposed."
        ),
    ),
    DocType.STATUS_REPORT: FactExtractionConfig(
        target_fact_types=[
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
        extraction_guidance=(
            "Extract completed work, blocked work, risks, next steps, owner updates, "
            "timeline changes, open questions, decisions, deliverables, and milestones."
        ),
        status_guidance=(
            "Status reports describe operational reality but usually do not override "
            "signed scope unless they cite an approved change."
        ),
    ),
    DocType.UNKNOWN: FactExtractionConfig(
        target_fact_types=[
            FactType.SCOPE_ITEM,
            FactType.OUT_OF_SCOPE_ITEM,
            FactType.REQUIREMENT,
            FactType.DATE,
            FactType.DECISION,
            FactType.CLIENT_REQUEST,
            FactType.RISK,
            FactType.OPEN_QUESTION,
            FactType.STAKEHOLDER,
            FactType.SYSTEM_OR_INTEGRATION,
        ],
        extraction_guidance=(
            "Extract only clearly stated project facts with strong evidence. Use "
            "caution because the document type is unknown."
        ),
        status_guidance=(
            "Use unknown or tentative fact statuses unless the text clearly indicates "
            "approval, signature, or rejection."
        ),
    ),
}
