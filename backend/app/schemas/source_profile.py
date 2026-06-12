from datetime import date, datetime

from pydantic import BaseModel, Field

from backend.app.schemas.common import AuthorityLevel
from backend.app.schemas.enums import (
    DocType,
    FactCategory,
    InferenceSource,
    ReliabilityFlag,
    SourceOrigin,
    SourceStatus,
)


class SourceProfileInput(BaseModel):
    document_id: str = Field(..., description="ID of the uploaded document.")
    user_provided_doc_type: DocType | None = None
    user_provided_origin: SourceOrigin | None = None
    user_provided_status: SourceStatus | None = None
    user_provided_recency_date: date | None = None


class DocumentMetadata(BaseModel):
    uploaded_at: datetime | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None


class ProfileSourceDocument(BaseModel):
    id: str
    text: str
    filename: str | None = None
    metadata: DocumentMetadata | None = None


class ProfileSourceArgs(BaseModel):
    document: ProfileSourceDocument
    input: SourceProfileInput | None = None


class SourceProfileInference(BaseModel):
    inferred_doc_type: DocType
    doc_type_confidence: float = Field(ge=0.0, le=1.0)

    inferred_origin: SourceOrigin
    origin_confidence: float = Field(ge=0.0, le=1.0)

    inferred_status: SourceStatus
    status_confidence: float = Field(ge=0.0, le=1.0)

    inferred_recency_date: date | None = None
    recency_date_confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    observed_content: list[FactCategory]

    reliability_flags: list[ReliabilityFlag]

    summary: str


class SourceProfile(BaseModel):
    id: str
    document_id: str

    doc_type: DocType
    doc_type_confidence: float = Field(ge=0.0, le=1.0)
    doc_type_source: InferenceSource

    origin: SourceOrigin
    origin_confidence: float = Field(ge=0.0, le=1.0)
    origin_source: InferenceSource

    status: SourceStatus
    status_confidence: float = Field(ge=0.0, le=1.0)
    status_source: InferenceSource

    authority_level: AuthorityLevel
    authority_rationale: str

    recency_date: date | None = None
    recency_date_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    recency_date_source: InferenceSource | None = None

    expected_content: list[FactCategory]
    observed_content: list[FactCategory]
    missing_expected_content: list[FactCategory]

    reliability_flags: list[ReliabilityFlag]

    summary: str
