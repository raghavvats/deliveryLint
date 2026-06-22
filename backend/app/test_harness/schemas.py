"""Schemas for the DeliveryLint test harness."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from backend.app.schemas.enums import DocType, LintFindingType


class ExpectedFinding(BaseModel):
    index: int
    acceptable_types: list[LintFindingType]
    description: str


class TestSuiteDefinition(BaseModel):
    id: str
    name: str
    directory: str
    target_filename: str
    target_doc_type: DocType
    expected_findings: list[ExpectedFinding]
    reference_count: int


class ActualFindingSnapshot(BaseModel):
    id: str
    finding_type: LintFindingType
    title: str
    message: str


class ExpectedFindingResult(BaseModel):
    index: int
    acceptable_types: list[LintFindingType]
    description: str
    caught: bool
    matched_finding_id: str | None = None
    matched_finding_type: LintFindingType | None = None
    matched_title: str | None = None
    match_score: float | None = None


class SuiteRunResult(BaseModel):
    suite_id: str
    suite_name: str
    target_filename: str
    target_doc_type: DocType
    status: str
    error_message: str | None = None
    expected_count: int = 0
    caught_count: int = 0
    missed_count: int = 0
    recall_pct: float = 0.0
    actual_finding_count: int = 0
    extra_finding_count: int = 0
    expected_results: list[ExpectedFindingResult] = Field(default_factory=list)
    extra_findings: list[ActualFindingSnapshot] = Field(default_factory=list)
    duration_ms: int | None = None


class HarnessRunStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    RUNNING = "running"


class HarnessRunSummary(BaseModel):
    id: int
    created_at: datetime
    status: HarnessRunStatus
    llm_provider: str
    suite_count: int
    total_expected: int
    total_caught: int
    recall_pct: float
    error_message: str | None = None


class HarnessRunDetail(BaseModel):
    id: int
    created_at: datetime
    status: HarnessRunStatus
    llm_provider: str
    suite_count: int
    total_expected: int
    total_caught: int
    missed_count: int
    recall_pct: float
    error_message: str | None = None
    suite_results: list[SuiteRunResult] = Field(default_factory=list)


class RunHarnessRequest(BaseModel):
    suite_ids: list[str] | None = None
