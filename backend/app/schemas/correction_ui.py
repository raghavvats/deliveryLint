from pydantic import BaseModel, Field

from backend.app.schemas.enums import (
    DocType,
    InferenceSource,
    LintFindingType,
    LintSeverity,
    ReviewPriority,
    SourceStatus,
)
from backend.app.schemas.fact_cluster import FactCluster
from backend.app.schemas.lint import LintEngineWarning, RunLintOutput
from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.source_profile import SourceProfile
from backend.app.schemas.target_document import TargetLocation, TargetProfile
from backend.app.schemas.target_parser import TargetParseResult


class CorrectionTargetDocument(BaseModel):
    id: str
    project_id: str

    filename: str | None = None
    text: str

    doc_type: DocType


class CorrectionUIInput(BaseModel):
    project_id: str

    target_document: CorrectionTargetDocument

    target_parse_result: TargetParseResult

    lint_output: RunLintOutput

    source_profiles: list[SourceProfile]
    project_facts: list[ProjectFact]
    fact_clusters: list[FactCluster]


class CorrectionSourceSummary(BaseModel):
    source_profile_id: str
    document_id: str

    doc_type: DocType
    authority_level: int
    status: SourceStatus
    summary: str


class CorrectionFindingView(BaseModel):
    id: str

    priority: ReviewPriority

    finding_type: LintFindingType
    severity: LintSeverity
    confidence: float

    title: str
    message: str
    recommendation: str | None = None

    target_quote: str | None = None
    reference_quotes: list[str] = []

    target_location: TargetLocation | None = None

    related_source_summaries: list[CorrectionSourceSummary] = []

    rule_id: str


class CorrectionSummary(BaseModel):
    total_findings: int

    needs_fix_count: int
    needs_review_count: int
    quality_suggestion_count: int
    info_count: int

    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    average_confidence: float | None = None

    has_blocking_issues: bool


class CorrectionUIResponse(BaseModel):
    project_id: str

    target_document: CorrectionTargetDocument

    target_profile: TargetProfile

    findings: list[CorrectionFindingView]

    lint_warnings: list[LintEngineWarning]

    summary: CorrectionSummary
