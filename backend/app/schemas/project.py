"""API schemas for project management."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from backend.app.schemas.analysis_run import AnalysisRunSummary
from backend.app.schemas.enums import DocType


class ReferenceDocumentStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ProjectSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    reference_count: int = 0
    target_count: int = 0
    processing_count: int = 0


class ReferenceDocumentSummary(BaseModel):
    id: str
    project_id: str
    filename: str
    doc_type: DocType
    created_at: datetime
    status: ReferenceDocumentStatus = ReferenceDocumentStatus.READY
    error_message: str | None = None


class ReferenceDocumentDetail(ReferenceDocumentSummary):
    text: str


class ProjectDetail(BaseModel):
    id: str
    name: str
    created_at: datetime
    references: list[ReferenceDocumentSummary]
    runs: list[AnalysisRunSummary]


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class TargetUploadResponse(BaseModel):
    analysis_run_id: int
    status: str
    project_id: str
