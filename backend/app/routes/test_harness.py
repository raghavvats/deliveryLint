"""API routes for the DeliveryLint test harness."""

import asyncio
from threading import Thread

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from backend.app.config.settings import get_settings
from backend.app.db.models import (
    clear_test_harness_runs,
    complete_test_harness_run,
    create_processing_test_harness_run,
    delete_test_harness_run,
    ensure_utc_datetime,
    fail_test_harness_run,
    get_test_harness_run_record,
    list_test_harness_runs,
)
from backend.app.test_harness.export import export_filename, render_harness_run_markdown
from backend.app.test_harness.runner import run_harness
from backend.app.test_harness.schemas import (
    HarnessRunDetail,
    HarnessRunStatus,
    HarnessRunSummary,
    RunHarnessRequest,
    TestSuiteDefinition,
)
from backend.app.test_harness.suite_loader import discover_suites, get_test_files_root

router = APIRouter(prefix="/test", tags=["test-harness"])


def _empty_summary(record) -> HarnessRunSummary:
    assert record.id is not None
    return HarnessRunSummary(
        id=record.id,
        created_at=ensure_utc_datetime(record.created_at),
        status=HarnessRunStatus(record.status),
        llm_provider=record.llm_provider,
        suite_count=0,
        total_expected=0,
        total_caught=0,
        recall_pct=0.0,
        error_message=record.error_message,
    )


def _empty_detail(record) -> HarnessRunDetail:
    assert record.id is not None
    return HarnessRunDetail(
        id=record.id,
        created_at=ensure_utc_datetime(record.created_at),
        status=HarnessRunStatus(record.status),
        llm_provider=record.llm_provider,
        suite_count=0,
        total_expected=0,
        total_caught=0,
        missed_count=0,
        recall_pct=0.0,
        error_message=record.error_message,
        suite_results=[],
    )


def _record_to_summary(record) -> HarnessRunSummary:
    if record.status == HarnessRunStatus.RUNNING.value:
        return _empty_summary(record)
    if not record.result_json or record.result_json == "{}":
        return _empty_summary(record)
    try:
        detail = HarnessRunDetail.model_validate_json(record.result_json)
    except Exception:
        return _empty_summary(record)
    assert record.id is not None
    return HarnessRunSummary(
        id=record.id,
        created_at=ensure_utc_datetime(record.created_at),
        status=HarnessRunStatus(record.status),
        llm_provider=record.llm_provider,
        suite_count=detail.suite_count,
        total_expected=detail.total_expected,
        total_caught=detail.total_caught,
        recall_pct=detail.recall_pct,
        error_message=record.error_message,
    )


def _record_to_detail(record) -> HarnessRunDetail:
    if record.status == HarnessRunStatus.RUNNING.value:
        return _empty_detail(record)
    if not record.result_json or record.result_json == "{}":
        return _empty_detail(record)
    try:
        detail = HarnessRunDetail.model_validate_json(record.result_json)
    except Exception:
        return _empty_detail(record)
    detail.id = record.id
    detail.created_at = ensure_utc_datetime(record.created_at)
    detail.status = HarnessRunStatus(record.status)
    detail.llm_provider = record.llm_provider
    detail.error_message = record.error_message
    return detail


async def _process_harness_run(run_id: int, suite_ids: list[str] | None) -> None:
    try:
        detail = await run_harness(suite_ids=suite_ids)
        complete_test_harness_run(
            run_id,
            detail.model_dump_json(),
            status=detail.status.value,
            error_message=detail.error_message,
        )
    except Exception as exc:  # noqa: BLE001 — persist failure for polling clients
        fail_test_harness_run(run_id, str(exc))


def _process_harness_run_in_thread(run_id: int, suite_ids: list[str] | None) -> None:
    asyncio.run(_process_harness_run(run_id, suite_ids))


@router.get("/suites", response_model=list[TestSuiteDefinition])
def list_suites() -> list[TestSuiteDefinition]:
    return discover_suites()


@router.get("/meta")
def harness_meta() -> dict[str, str | int]:
    root = get_test_files_root()
    suites = discover_suites()
    return {
        "test_files_root": str(root),
        "suite_count": len(suites),
        "exists": root.is_dir(),
    }


@router.post("/runs", response_model=HarnessRunDetail)
async def create_harness_run(request: RunHarnessRequest | None = None) -> HarnessRunDetail:
    suite_ids = request.suite_ids if request else None
    if suite_ids:
        known = {suite.id for suite in discover_suites()}
        missing = [suite_id for suite_id in suite_ids if suite_id not in known]
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown suite id(s): {', '.join(missing)}")

    settings = get_settings()
    record = create_processing_test_harness_run(llm_provider=settings.llm_provider)
    assert record.id is not None

    Thread(
        target=_process_harness_run_in_thread,
        kwargs={"run_id": record.id, "suite_ids": suite_ids},
        daemon=True,
    ).start()

    return _record_to_detail(record)


@router.get("/runs", response_model=list[HarnessRunSummary])
def list_harness_runs(limit: int = Query(default=50, ge=1, le=200)) -> list[HarnessRunSummary]:
    records = list_test_harness_runs(limit=limit)
    return [_record_to_summary(record) for record in records if record.id is not None]


@router.get("/runs/{run_id}", response_model=HarnessRunDetail)
def get_harness_run(run_id: int) -> HarnessRunDetail:
    record = get_test_harness_run_record(run_id)
    if record is None or record.id is None:
        raise HTTPException(status_code=404, detail="Test harness run not found")
    return _record_to_detail(record)


@router.get("/runs/{run_id}/export.md")
def export_harness_run_markdown(run_id: int) -> PlainTextResponse:
    record = get_test_harness_run_record(run_id)
    if record is None or record.id is None:
        raise HTTPException(status_code=404, detail="Test harness run not found")

    detail = _record_to_detail(record)
    if detail.status == HarnessRunStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Run still in progress; export when complete")

    markdown = render_harness_run_markdown(detail)
    filename = export_filename(run_id)
    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/runs/{run_id}")
def delete_harness_run(run_id: int) -> dict[str, int]:
    if not delete_test_harness_run(run_id):
        raise HTTPException(status_code=404, detail="Test harness run not found")
    return {"deleted": run_id}


@router.delete("/runs")
def delete_all_harness_runs() -> dict[str, int]:
    deleted = clear_test_harness_runs()
    return {"deleted": deleted}
