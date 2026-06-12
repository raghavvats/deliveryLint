from datetime import date

from pydantic import BaseModel, Field

from backend.app.schemas.common import AuthorityLevel
from backend.app.schemas.enums import (
    DateType,
    DependencyType,
    DocType,
    FactPolarity,
    FactStatus,
    FactType,
    Priority,
    RiskLevel,
    SourceStatus,
)


class ProjectFactAttributes(BaseModel):
    date_type: DateType | None = None
    date_value: date | None = None

    owner: str | None = None

    priority: Priority | None = None

    system: str | None = None

    requirement_id: str | None = None
    test_id: str | None = None
    linked_requirement_ids: list[str] | None = None

    stakeholder_role: str | None = None

    dependency_type: DependencyType | None = None

    risk_level: RiskLevel | None = None


class EvidenceSpan(BaseModel):
    quote: str = Field(..., min_length=1)

    section_title: str | None = None

    page: int | None = Field(default=None, ge=1)

    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)

    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

    timestamp: str | None = None


class ProjectFact(BaseModel):
    id: str
    project_id: str
    document_id: str
    source_profile_id: str

    fact_type: FactType

    text: str = Field(..., min_length=1)

    subject: str = Field(..., min_length=1)

    normalized_subject: str = Field(..., min_length=1)

    polarity: FactPolarity

    fact_status: FactStatus

    attributes: ProjectFactAttributes | None = None

    evidence: EvidenceSpan

    source_authority_level: AuthorityLevel
    source_doc_type: DocType
    source_status: SourceStatus

    extraction_confidence: float = Field(ge=0.0, le=1.0)
