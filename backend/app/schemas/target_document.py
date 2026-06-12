from pydantic import BaseModel, Field

from backend.app.schemas.enums import (
    DocType,
    FactCategory,
    FactPolarity,
    FactStatus,
    FactType,
    InferenceSource,
    TargetQualityFlag,
)
from backend.app.schemas.project_fact import ProjectFactAttributes


class TargetLocation(BaseModel):
    quote: str | None = None

    section_title: str | None = None

    page: int | None = Field(default=None, ge=1)

    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)

    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)


class TargetProfile(BaseModel):
    document_id: str

    doc_type: DocType
    doc_type_confidence: float = Field(ge=0.0, le=1.0)
    doc_type_source: InferenceSource

    expected_content: list[FactCategory]
    observed_content: list[FactCategory]
    missing_expected_content: list[FactCategory]

    target_rubric_id: str

    quality_flags: list[TargetQualityFlag]


class TargetSection(BaseModel):
    id: str
    document_id: str

    title: str
    normalized_title: str

    text: str

    content_categories: list[FactCategory]

    location: TargetLocation


class TargetClaim(BaseModel):
    id: str
    project_id: str
    document_id: str

    claim_type: FactType

    text: str = Field(..., min_length=1)

    subject: str = Field(..., min_length=1)

    normalized_subject: str = Field(..., min_length=1)

    polarity: FactPolarity

    claim_status: FactStatus

    attributes: ProjectFactAttributes | None = None

    location: TargetLocation

    checkable: bool

    non_checkable_reason: str | None = None

    extraction_confidence: float = Field(ge=0.0, le=1.0)
