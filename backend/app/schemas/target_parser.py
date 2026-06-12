from enum import Enum

from pydantic import BaseModel, Field

from backend.app.schemas.enums import (
    DocType,
    FactCategory,
    FactPolarity,
    FactStatus,
    FactType,
    InferenceSource,
)
from backend.app.schemas.project_fact import ProjectFactAttributes
from backend.app.schemas.target_document import (
    TargetClaim,
    TargetLocation,
    TargetProfile,
    TargetSection,
)


class TargetParserDocument(BaseModel):
    id: str
    text: str
    filename: str | None = None


class ParseTargetDocumentInput(BaseModel):
    project_id: str
    document: TargetParserDocument

    target_doc_type: DocType
    target_doc_type_source: InferenceSource = InferenceSource.USER
    target_doc_type_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class TargetParseWarningCode(str, Enum):
    NO_CLAIMS_EXTRACTED = "NO_CLAIMS_EXTRACTED"
    NO_SECTIONS_DETECTED = "NO_SECTIONS_DETECTED"
    MISSING_EXPECTED_CONTENT = "MISSING_EXPECTED_CONTENT"
    LOW_CONFIDENCE_EXTRACTION = "LOW_CONFIDENCE_EXTRACTION"
    TARGET_TYPE_NOT_ELIGIBLE = "TARGET_TYPE_NOT_ELIGIBLE"
    UNSUPPORTED_CLAIM_DROPPED = "UNSUPPORTED_CLAIM_DROPPED"
    TARGET_LOCATION_MISSING = "TARGET_LOCATION_MISSING"


class TargetParseWarning(BaseModel):
    code: TargetParseWarningCode
    message: str
    related_claim_type: FactType | None = None
    related_content_category: FactCategory | None = None


class TargetParseResult(BaseModel):
    target_profile: TargetProfile
    sections: list[TargetSection]
    claims: list[TargetClaim]
    warnings: list[TargetParseWarning]


class TargetSectionLLMOutput(BaseModel):
    title: str
    normalized_title: str
    text: str
    content_categories: list[FactCategory]

    location: TargetLocation


class TargetClaimLLMOutput(BaseModel):
    claim_type: FactType

    text: str
    subject: str
    normalized_subject: str

    polarity: FactPolarity
    claim_status: FactStatus

    attributes: ProjectFactAttributes | None = None

    location: TargetLocation

    checkable: bool
    non_checkable_reason: str | None = None

    extraction_confidence: float = Field(ge=0.0, le=1.0)


class TargetDocumentLLMResponse(BaseModel):
    observed_content: list[FactCategory]
    sections: list[TargetSectionLLMOutput]
    claims: list[TargetClaimLLMOutput]
    warnings: list[TargetParseWarning] = []
