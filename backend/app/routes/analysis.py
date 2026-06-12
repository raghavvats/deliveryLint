"""FastAPI analysis routes."""

from fastapi import APIRouter, Query

from backend.app.db.models import save_analysis_run
from backend.app.pipeline.run_pipeline import run_full_pipeline
from backend.app.schemas.pipeline import PipelineResult

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/lint", response_model=PipelineResult)
async def run_analysis_lint(
    include_debug: bool = Query(default=False),
    persist: bool = Query(default=False),
) -> PipelineResult:
    """Run the in-memory sample pipeline and return CorrectionUIResponse."""
    result = await run_full_pipeline(include_debug=include_debug)
    if persist:
        save_analysis_run(
            project_id=result.correction_ui_response.project_id,
            response_json=result.correction_ui_response.model_dump_json(),
        )
    return result
