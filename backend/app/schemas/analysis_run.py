"""API schemas for persisted analysis runs."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.schemas.correction_ui import CorrectionUIResponse


class AnalysisRunSummary(BaseModel):
    id: int
    project_id: str
    created_at: datetime


class AnalysisRunDetail(AnalysisRunSummary):
    correction_ui_response: CorrectionUIResponse
