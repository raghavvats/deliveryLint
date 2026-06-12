from enum import Enum

from pydantic import BaseModel, Field

from backend.app.schemas.enums import LintFindingType, LintSeverity
from backend.app.schemas.fact_cluster import FactCluster
from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.source_profile import SourceProfile
from backend.app.schemas.target_document import TargetLocation, TargetProfile, TargetSection, TargetClaim
from backend.app.schemas.target_parser import TargetParseResult


class LintEngineWarningCode(str, Enum):
    NO_REFERENCE_FACTS = "NO_REFERENCE_FACTS"
    NO_SOURCE_PROFILES = "NO_SOURCE_PROFILES"
    NO_FACT_CLUSTERS = "NO_FACT_CLUSTERS"
    CHECK_SKIPPED_INSUFFICIENT_EVIDENCE = "CHECK_SKIPPED_INSUFFICIENT_EVIDENCE"
    LOW_REFERENCE_COVERAGE = "LOW_REFERENCE_COVERAGE"


class LintEngineWarning(BaseModel):
    code: LintEngineWarningCode
    message: str


class LintFinding(BaseModel):
    id: str
    project_id: str
    target_document_id: str

    finding_type: LintFindingType
    severity: LintSeverity
    confidence: float = Field(ge=0.0, le=1.0)

    title: str
    message: str

    target_claim_id: str | None = None
    target_section_id: str | None = None
    target_location: TargetLocation | None = None

    related_fact_ids: list[str] = []
    related_fact_cluster_ids: list[str] = []
    related_source_profile_ids: list[str] = []

    target_quote: str | None = None
    reference_quotes: list[str] = []

    recommendation: str | None = None

    rule_id: str


class RunLintInput(BaseModel):
    project_id: str

    target_parse_result: TargetParseResult

    source_profiles: list[SourceProfile]
    project_facts: list[ProjectFact]
    fact_clusters: list[FactCluster]


class RunLintOutput(BaseModel):
    findings: list[LintFinding]
    warnings: list[LintEngineWarning]


class LintContext(BaseModel):
    project_id: str
    target_parse_result: TargetParseResult

    source_profiles: list[SourceProfile]
    project_facts: list[ProjectFact]
    fact_clusters: list[FactCluster]

    @property
    def target_profile(self) -> TargetProfile:
        return self.target_parse_result.target_profile

    @property
    def target_sections(self) -> list[TargetSection]:
        return self.target_parse_result.sections

    @property
    def target_claims(self) -> list[TargetClaim]:
        return self.target_parse_result.claims

    model_config = {"arbitrary_types_allowed": True}
