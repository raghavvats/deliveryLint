"""API schemas for persisted analysis runs."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from backend.app.schemas.correction_ui import CorrectionUIResponse


class AnalysisRunStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RunFindingsSummary(BaseModel):
    total_findings: int
    needs_fix_count: int
    needs_review_count: int
    has_blocking_issues: bool


class AnalysisRunSummary(BaseModel):
    id: int
    project_id: str
    name: str
    created_at: datetime
    status: AnalysisRunStatus = AnalysisRunStatus.COMPLETED
    error_message: str | None = None
    findings_summary: RunFindingsSummary | None = None


class AnalysisRunDetail(AnalysisRunSummary):
    correction_ui_response: CorrectionUIResponse | None = None


class UpdateAnalysisRunRequest(BaseModel):
    name: str
