from pydantic import BaseModel

from backend.app.schemas.correction_ui import CorrectionUIResponse
from backend.app.schemas.fact_cluster import FactCluster
from backend.app.schemas.fact_parser import ExtractProjectFactsOutput
from backend.app.schemas.lint import RunLintOutput
from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.source_profile import SourceProfile
from backend.app.schemas.target_parser import TargetParseResult


class PipelineDebugContext(BaseModel):
    source_profiles: list[SourceProfile]
    extract_outputs: list[ExtractProjectFactsOutput]
    project_facts: list[ProjectFact]
    fact_clusters: list[FactCluster]
    target_parse_result: TargetParseResult
    run_lint_output: RunLintOutput


class PipelineResult(BaseModel):
    correction_ui_response: CorrectionUIResponse
    run_lint_output: RunLintOutput | None = None
    debug: PipelineDebugContext | None = None
    analysis_run_id: int | None = None
