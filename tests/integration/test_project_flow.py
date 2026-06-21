import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.db.models import (
    complete_analysis_run,
    create_processing_run,
    get_analysis_run,
    list_reference_documents,
    save_reference_document,
)
from backend.app.main import create_app
from backend.app.pipeline.run_pipeline import run_reference_document_pipeline, run_target_against_cached_references
from backend.app.schemas.upload import build_reference_profile_input
from tests.fixtures.northstar_pipeline import build_northstar_mock_client, build_northstar_request


@pytest.fixture
def client(tmp_path, monkeypatch):
    from backend.app.config.settings import get_settings

    db_url = f"sqlite:///{tmp_path / 'api.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()
    return TestClient(create_app())


def test_target_upload_returns_before_processing_finishes(client, tmp_path, monkeypatch) -> None:
    from backend.app.config.settings import get_settings

    db_url = f"sqlite:///{tmp_path / 'fast_target.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()

    create_resp = client.post("/projects", json={"name": "Fast target"})
    project_id = create_resp.json()["id"]

    async def slow_pipeline(**_kwargs):
        await asyncio.sleep(2)
        raise AssertionError("should not be awaited by the HTTP handler")

    with patch(
        "backend.app.routes.projects.run_target_against_cached_references",
        new=AsyncMock(side_effect=slow_pipeline),
    ):
        started = time.monotonic()
        response = client.post(
            f"/projects/{project_id}/targets",
            files={"target_file": ("target.txt", b"Sample target text.", "text/plain")},
            data={"target_doc_type": "DRAFT_SOW"},
        )
        elapsed = time.monotonic() - started

    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert elapsed < 1.0


def test_reference_upload_returns_before_processing_finishes(client, tmp_path, monkeypatch) -> None:
    from backend.app.config.settings import get_settings

    db_url = f"sqlite:///{tmp_path / 'fast_reference.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()

    create_resp = client.post("/projects", json={"name": "Fast reference"})
    project_id = create_resp.json()["id"]

    async def slow_pipeline(**_kwargs):
        await asyncio.sleep(2)
        raise AssertionError("should not be awaited by the HTTP handler")

    with patch(
        "backend.app.routes.projects.run_reference_document_pipeline",
        new=AsyncMock(side_effect=slow_pipeline),
    ):
        started = time.monotonic()
        response = client.post(
            f"/projects/{project_id}/references",
            files={"reference_file": ("signed.txt", b"Signed scope text.", "text/plain")},
        )
        elapsed = time.monotonic() - started

    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert elapsed < 1.0


def test_project_reference_and_async_target_flow(client, tmp_path, monkeypatch) -> None:
    from backend.app.config.settings import get_settings

    db_url = f"sqlite:///{tmp_path / 'api.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()

    create_resp = client.post("/projects", json={"name": "Northstar"})
    assert create_resp.status_code == 200
    project_id = create_resp.json()["id"]

    request = build_northstar_request(project_id)
    reference = request.references[0]
    ref_id = reference.resolved_id()

    profile, extract_output, _ = asyncio.run(
        run_reference_document_pipeline(
            project_id=project_id,
            document_id=ref_id,
            text=reference.text,
            filename=reference.filename,
            profile_input=build_reference_profile_input(ref_id, reference),
            llm_client=build_northstar_mock_client(),
        )
    )
    save_reference_document(
        project_id=project_id,
        filename=reference.filename,
        text=reference.text,
        profile_hints_json="{}",
        cached_profile=profile,
        cached_facts=extract_output.facts,
        database_url=db_url,
    )

    run_record = create_processing_run(project_id, name="draft.txt", database_url=db_url)
    assert run_record.id is not None

    result = asyncio.run(
        run_target_against_cached_references(
            project_id=project_id,
            target=request.target,
            target_doc_type=request.target_doc_type,
            cached_references=list_reference_documents(project_id, database_url=db_url),
            llm_client=build_northstar_mock_client(),
        )
    )
    complete_analysis_run(
        run_record.id,
        result.correction_ui_response.model_dump_json(),
        name="draft.txt",
        database_url=db_url,
    )

    detail = get_analysis_run(run_record.id, database_url=db_url)
    assert detail is not None
    assert detail.status.value == "completed"
    assert detail.correction_ui_response is not None
    assert detail.correction_ui_response.reference_documents
    assert detail.correction_ui_response.findings

    project_detail = client.get(f"/projects/{project_id}")
    assert project_detail.status_code == 200
    assert len(project_detail.json()["references"]) == 1
    assert len(project_detail.json()["runs"]) == 1
