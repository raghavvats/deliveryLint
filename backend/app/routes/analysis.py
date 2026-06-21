"""FastAPI analysis routes."""

import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import ValidationError

from backend.app.db.models import (
    clear_analysis_runs,
    delete_analysis_run,
    get_analysis_run,
    list_analysis_runs,
    save_analysis_run,
    update_analysis_run_name,
)
from backend.app.pipeline.run_pipeline import run_custom_pipeline, run_full_pipeline
from backend.app.schemas.analysis_run import AnalysisRunDetail, AnalysisRunSummary, UpdateAnalysisRunRequest
from backend.app.schemas.enums import DocType
from backend.app.schemas.pipeline import PipelineResult
from backend.app.schemas.upload import (
    CustomLintRequest,
    ReferenceProfileHints,
    ReferenceUpload,
    UploadedDocument,
)
from backend.app.services.upload import read_upload_as_text

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _resolve_run_name(run_name: str | None, result: PipelineResult) -> str:
    if run_name and run_name.strip():
        return run_name.strip()
    filename = result.correction_ui_response.target_document.filename
    if filename:
        return filename
    return datetime.now(UTC).strftime("Run %Y-%m-%d %H:%M UTC")


def _persist_result(
    result: PipelineResult,
    *,
    include_debug: bool,
    run_name: str | None = None,
) -> PipelineResult:
    record = save_analysis_run(
        project_id=result.correction_ui_response.project_id,
        name=_resolve_run_name(run_name, result),
        response_json=result.correction_ui_response.model_dump_json(),
    )
    result.analysis_run_id = record.id
    if not include_debug:
        result.run_lint_output = None
        result.debug = None
    return result


def _parse_reference_metadata(raw_metadata: str) -> list[ReferenceProfileHints]:
    if not raw_metadata.strip():
        return []
    try:
        payload = json.loads(raw_metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="reference_metadata must be valid JSON") from exc
    if not isinstance(payload, list):
        raise HTTPException(status_code=400, detail="reference_metadata must be a JSON array")
    try:
        return [ReferenceProfileHints.model_validate(item) for item in payload]
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


@router.post("/lint", response_model=PipelineResult)
async def run_analysis_lint(
    include_debug: bool = Query(default=False),
    run_name: str | None = Query(default=None),
) -> PipelineResult:
    """Run the built-in sample pipeline and return CorrectionUIResponse."""
    result = await run_full_pipeline(include_debug=include_debug)
    return _persist_result(result, include_debug=include_debug, run_name=run_name)


@router.post("/lint/custom", response_model=PipelineResult)
async def run_custom_analysis_lint(
    request: CustomLintRequest,
    include_debug: bool = Query(default=False),
) -> PipelineResult:
    """Run lint analysis on user-provided document text."""
    result = await run_custom_pipeline(request, include_debug=include_debug)
    return _persist_result(result, include_debug=include_debug, run_name=request.run_name)


@router.post("/lint/upload", response_model=PipelineResult)
async def run_uploaded_analysis_lint(
    target_file: UploadFile = File(...),
    target_doc_type: DocType = Form(DocType.DRAFT_SOW),
    reference_files: list[UploadFile] = File(default=[]),
    reference_metadata: str = Form(default="[]"),
    project_id: str | None = Form(default=None),
    run_name: str | None = Form(default=None),
    include_debug: bool = Query(default=False),
) -> PipelineResult:
    """Run lint analysis on uploaded text documents (.txt, .md)."""
    target_filename, target_text = await read_upload_as_text(target_file)
    metadata = _parse_reference_metadata(reference_metadata)

    if metadata and len(metadata) != len(reference_files):
        raise HTTPException(
            status_code=400,
            detail="reference_metadata must have one entry per reference file",
        )

    references: list[ReferenceUpload] = []
    for index, reference_file in enumerate(reference_files):
        filename, text = await read_upload_as_text(reference_file)
        hints = metadata[index] if index < len(metadata) else None
        references.append(
            ReferenceUpload(filename=filename, text=text, profile_hints=hints),
        )

    request = CustomLintRequest(
        project_id=project_id or f"project_{uuid4().hex[:8]}",
        run_name=run_name,
        target=UploadedDocument(filename=target_filename, text=target_text),
        target_doc_type=target_doc_type,
        references=references,
    )
    result = await run_custom_pipeline(request, include_debug=include_debug)
    return _persist_result(result, include_debug=include_debug, run_name=run_name)


@router.get("/runs", response_model=list[AnalysisRunSummary])
def list_runs(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AnalysisRunSummary]:
    return list_analysis_runs(project_id=project_id, limit=limit)


@router.delete("/runs")
def delete_all_runs() -> dict[str, int]:
    deleted = clear_analysis_runs()
    return {"deleted": deleted}


@router.delete("/runs/{run_id}")
def delete_run(run_id: int) -> dict[str, int]:
    if not delete_analysis_run(run_id):
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return {"deleted": run_id}


@router.patch("/runs/{run_id}", response_model=AnalysisRunSummary)
def rename_run(run_id: int, request: UpdateAnalysisRunRequest) -> AnalysisRunSummary:
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Run name cannot be empty")
    record = update_analysis_run_name(run_id, name)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return record


@router.get("/runs/{run_id}", response_model=AnalysisRunDetail)
def get_run(run_id: int) -> AnalysisRunDetail:
    record = get_analysis_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return record
