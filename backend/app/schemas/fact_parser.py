from enum import Enum

from pydantic import BaseModel, Field

from backend.app.schemas.enums import FactPolarity, FactStatus, FactType
from backend.app.schemas.project_fact import (
    EvidenceSpan,
    ProjectFact,
    ProjectFactAttributes,
)
from backend.app.schemas.source_profile import SourceProfile


class FactParserDocument(BaseModel):
    id: str
    text: str
    filename: str | None = None


class ExtractProjectFactsInput(BaseModel):
    project_id: str
    document: FactParserDocument
    source_profile: SourceProfile


class FactExtractionWarningCode(str, Enum):
    NO_FACTS_EXTRACTED = "NO_FACTS_EXTRACTED"
    EXPECTED_CONTENT_NOT_FOUND = "EXPECTED_CONTENT_NOT_FOUND"
    LOW_CONFIDENCE_EXTRACTION = "LOW_CONFIDENCE_EXTRACTION"
    EVIDENCE_LOCATION_MISSING = "EVIDENCE_LOCATION_MISSING"
    UNSUPPORTED_FACT_DROPPED = "UNSUPPORTED_FACT_DROPPED"
    UNKNOWN_DOC_TYPE_EXTRACTION = "UNKNOWN_DOC_TYPE_EXTRACTION"


class FactExtractionWarning(BaseModel):
    code: FactExtractionWarningCode
    message: str
    related_fact_type: FactType | None = None


class ExtractProjectFactsOutput(BaseModel):
    facts: list[ProjectFact]
    warnings: list[FactExtractionWarning]


class ProjectFactLLMOutput(BaseModel):
    fact_type: FactType

    text: str
    subject: str
    normalized_subject: str

    polarity: FactPolarity
    fact_status: FactStatus

    attributes: ProjectFactAttributes | None = None

    evidence: EvidenceSpan

    extraction_confidence: float = Field(ge=0.0, le=1.0)


class ProjectFactLLMResponse(BaseModel):
    facts: list[ProjectFactLLMOutput]
    warnings: list[FactExtractionWarning] = []
