"""FastAPI project routes."""

import asyncio
import json
from threading import Thread

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from backend.app.db.models import (
    complete_analysis_run,
    complete_reference_record,
    create_pending_reference_record,
    create_processing_run,
    create_project,
    delete_project,
    delete_reference_document,
    fail_analysis_run,
    fail_reference_record,
    get_analysis_run_record,
    get_project,
    get_project_detail,
    get_reference_document,
    list_completed_run_records,
    list_projects,
    list_ready_reference_documents,
    mark_analysis_run_processing,
)
from backend.app.pipeline.run_pipeline import run_reference_document_pipeline, run_target_against_cached_references
from backend.app.schemas.correction_ui import CorrectionUIResponse
from backend.app.schemas.enums import DocType
from backend.app.schemas.project import (
    CreateProjectRequest,
    ProjectDetail,
    ProjectSummary,
    ReferenceDocumentDetail,
    ReferenceDocumentSummary,
    ReferenceDocumentStatus,
    TargetUploadResponse,
)
from backend.app.schemas.upload import ReferenceProfileHints, ReferenceUpload, UploadedDocument, build_reference_profile_input
from backend.app.services.upload import read_upload_as_text

router = APIRouter(prefix="/projects", tags=["projects"])


def _parse_reference_metadata(raw_metadata: str) -> ReferenceProfileHints | None:
    if not raw_metadata.strip():
        return None
    try:
        payload = json.loads(raw_metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="reference_metadata must be valid JSON") from exc
    try:
        return ReferenceProfileHints.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _resolve_run_name(run_name: str | None, filename: str) -> str:
    if run_name and run_name.strip():
        return run_name.strip()
    return filename


def _target_from_run_record(record) -> tuple[UploadedDocument, DocType, str]:
    correction = CorrectionUIResponse.model_validate_json(record.response_json)
    filename = correction.target_document.filename or record.name
    target = UploadedDocument(
        filename=filename,
        text=correction.target_document.text,
        document_id=correction.target_document.id,
    )
    return target, correction.target_document.doc_type, record.name


async def _process_target_upload(
    *,
    run_id: int,
    project_id: str,
    target: UploadedDocument,
    target_doc_type: DocType,
    run_name: str | None,
) -> None:
    mark_analysis_run_processing(run_id)
    try:
        cached_refs = list_ready_reference_documents(project_id)
        result = await run_target_against_cached_references(
            project_id=project_id,
            target=target,
            target_doc_type=target_doc_type,
            cached_references=cached_refs,
        )
        name = _resolve_run_name(run_name, target.filename)
        complete_analysis_run(
            run_id,
            result.correction_ui_response.model_dump_json(),
            name=name,
        )
    except Exception as exc:  # noqa: BLE001 — persist failure for polling clients
        fail_analysis_run(run_id, str(exc))


def _process_target_upload_in_thread(**kwargs) -> None:
    """Run lint in a worker thread so the HTTP response can return immediately."""
    asyncio.run(_process_target_upload(**kwargs))


def _rerun_completed_runs_for_project(project_id: str) -> None:
    for record in list_completed_run_records(project_id):
        assert record.id is not None
        try:
            target, target_doc_type, run_name = _target_from_run_record(record)
        except Exception:
            continue
        Thread(
            target=_process_target_upload_in_thread,
            kwargs={
                "run_id": record.id,
                "project_id": project_id,
                "target": target,
                "target_doc_type": target_doc_type,
                "run_name": run_name,
            },
            daemon=True,
        ).start()


async def _process_reference_upload(
    *,
    ref_id: str,
    project_id: str,
    document_id: str,
    filename: str,
    text: str,
    profile_input,
) -> None:
    try:
        profile, extract_output, _ = await run_reference_document_pipeline(
            project_id=project_id,
            document_id=document_id,
            text=text,
            filename=filename,
            profile_input=profile_input,
        )
        complete_reference_record(
            ref_id,
            cached_profile=profile,
            cached_facts=extract_output.facts,
        )
        _rerun_completed_runs_for_project(project_id)
    except Exception as exc:  # noqa: BLE001 — persist failure for polling clients
        fail_reference_record(ref_id, str(exc))


def _process_reference_upload_in_thread(**kwargs) -> None:
    asyncio.run(_process_reference_upload(**kwargs))


@router.post("", response_model=ProjectSummary)
async def create_project_route(request: CreateProjectRequest) -> ProjectSummary:
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty")
    record = create_project(name)
    return ProjectSummary(
        id=record.id,
        name=record.name,
        created_at=record.created_at,
        reference_count=0,
        target_count=0,
        processing_count=0,
    )


@router.get("", response_model=list[ProjectSummary])
def list_projects_route() -> list[ProjectSummary]:
    return list_projects()


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project_route(project_id: str) -> ProjectDetail:
    detail = get_project_detail(project_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail


@router.delete("/{project_id}")
def delete_project_route(project_id: str) -> dict[str, str]:
    if not delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": project_id}


@router.post("/{project_id}/references", response_model=ReferenceDocumentSummary)
async def upload_reference_route(
    project_id: str,
    reference_file: UploadFile = File(...),
    reference_metadata: str = Form(default=""),
) -> ReferenceDocumentSummary:
    if get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    filename, text = await read_upload_as_text(reference_file)
    hints = _parse_reference_metadata(reference_metadata)

    reference = ReferenceUpload(filename=filename, text=text, profile_hints=hints)
    document_id = reference.resolved_id()
    profile_input = build_reference_profile_input(document_id, reference)
    hints_json = hints.model_dump_json() if hints else "{}"

    record = create_pending_reference_record(
        project_id=project_id,
        filename=filename,
        text=text,
        profile_document_id=document_id,
        profile_hints_json=hints_json,
    )

    Thread(
        target=_process_reference_upload_in_thread,
        kwargs={
            "ref_id": record.id,
            "project_id": project_id,
            "document_id": document_id,
            "filename": filename,
            "text": text,
            "profile_input": profile_input,
        },
        daemon=True,
    ).start()

    return ReferenceDocumentSummary(
        id=record.id,
        project_id=project_id,
        filename=filename,
        doc_type=DocType.UNKNOWN,
        created_at=record.created_at,
        status=ReferenceDocumentStatus.PROCESSING,
    )


@router.get("/{project_id}/references/{ref_id}", response_model=ReferenceDocumentDetail)
def get_reference_route(project_id: str, ref_id: str) -> ReferenceDocumentDetail:
    detail = get_reference_document(project_id, ref_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Reference document not found")
    return detail


@router.delete("/{project_id}/references/{ref_id}")
def delete_reference_route(project_id: str, ref_id: str) -> dict[str, str]:
    if not delete_reference_document(project_id, ref_id):
        raise HTTPException(status_code=404, detail="Reference document not found")
    return {"deleted": ref_id}


@router.post("/{project_id}/targets", response_model=TargetUploadResponse)
async def upload_target_route(
    project_id: str,
    target_file: UploadFile = File(...),
    target_doc_type: DocType = Form(DocType.DRAFT_SOW),
    run_name: str | None = Form(default=None),
) -> TargetUploadResponse:
    if get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    filename, text = await read_upload_as_text(target_file)
    target = UploadedDocument(filename=filename, text=text)
    name = _resolve_run_name(run_name, filename)

    run_record = create_processing_run(project_id, name=name)
    if run_record.id is None:
        raise HTTPException(status_code=500, detail="Failed to create analysis run")

    Thread(
        target=_process_target_upload_in_thread,
        kwargs={
            "run_id": run_record.id,
            "project_id": project_id,
            "target": target,
            "target_doc_type": target_doc_type,
            "run_name": run_name,
        },
        daemon=True,
    ).start()

    assert run_record.id is not None
    return TargetUploadResponse(
        analysis_run_id=run_record.id,
        status="processing",
        project_id=project_id,
    )


@router.post("/{project_id}/runs/{run_id}/rerun", response_model=TargetUploadResponse)
async def rerun_target_route(
    project_id: str,
    run_id: int,
    target_file: UploadFile = File(...),
    target_doc_type: DocType | None = Form(default=None),
) -> TargetUploadResponse:
    if get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    record = get_analysis_run_record(run_id)
    if record is None or record.project_id != project_id:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    filename, text = await read_upload_as_text(target_file)
    target = UploadedDocument(filename=filename, text=text)

    resolved_doc_type = target_doc_type
    if resolved_doc_type is None and record.response_json:
        try:
            _, resolved_doc_type, _ = _target_from_run_record(record)
        except Exception:
            resolved_doc_type = DocType.DRAFT_SOW
    if resolved_doc_type is None:
        resolved_doc_type = DocType.DRAFT_SOW

    run_name = _resolve_run_name(None, filename)

    mark_analysis_run_processing(run_id)
    Thread(
        target=_process_target_upload_in_thread,
        kwargs={
            "run_id": run_id,
            "project_id": project_id,
            "target": target,
            "target_doc_type": resolved_doc_type,
            "run_name": run_name,
        },
        daemon=True,
    ).start()

    return TargetUploadResponse(
        analysis_run_id=run_id,
        status="processing",
        project_id=project_id,
    )
