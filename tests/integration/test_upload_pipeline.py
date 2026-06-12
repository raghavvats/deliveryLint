import io

import pytest
from fastapi.testclient import TestClient

from backend.app.fixtures.sample_documents import (
    CLIENT_EMAIL_TEXT,
    DRAFT_SOW_TARGET_TEXT,
    SIGNED_SOW_TEXT,
)
from backend.app.main import create_app
from backend.app.schemas.enums import DocType, SourceOrigin, SourceStatus
from backend.app.schemas.upload import (
    CustomLintRequest,
    ReferenceProfileHints,
    ReferenceUpload,
    UploadedDocument,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_custom_lint_request_validation() -> None:
    with pytest.raises(ValueError, match="empty"):
        UploadedDocument(filename="empty.txt", text="   ")


@pytest.mark.asyncio
async def test_run_custom_pipeline_with_mock_llm() -> None:
    from backend.app.fixtures.mock_pipeline_outputs import (
        MOCK_FACT_RESPONSES,
        MOCK_SOURCE_INFERENCES,
        MOCK_TARGET_RESPONSES,
    )
    from backend.app.fixtures.sample_documents import (
        CLIENT_EMAIL_DOC_ID,
        SIGNED_SOW_DOC_ID,
        TARGET_DOC_ID,
    )
    from backend.app.pipeline.run_pipeline import run_custom_pipeline
    from backend.app.services.llm_client import MockLLMClient

    llm_client = MockLLMClient(
        source_inferences=MOCK_SOURCE_INFERENCES,
        fact_responses=MOCK_FACT_RESPONSES,
        target_responses=MOCK_TARGET_RESPONSES,
    )

    result = await run_custom_pipeline(
        CustomLintRequest(
            project_id="custom_test",
            target=UploadedDocument(
                document_id=TARGET_DOC_ID,
                filename="draft_sow.txt",
                text=DRAFT_SOW_TARGET_TEXT,
            ),
            target_doc_type=DocType.DRAFT_SOW,
            references=[
                ReferenceUpload(
                    document_id=SIGNED_SOW_DOC_ID,
                    filename="signed_sow.txt",
                    text=SIGNED_SOW_TEXT,
                ),
                ReferenceUpload(
                    document_id=CLIENT_EMAIL_DOC_ID,
                    filename="client_email.txt",
                    text=CLIENT_EMAIL_TEXT,
                ),
            ],
        ),
        llm_client=llm_client,
    )

    assert result.correction_ui_response.project_id == "custom_test"
    assert result.correction_ui_response.summary.total_findings > 0


def test_upload_endpoint_accepts_reference_metadata(client: TestClient) -> None:
    response = client.post(
        "/analysis/lint/upload",
        data={
            "target_doc_type": DocType.DRAFT_SOW.value,
            "reference_metadata": (
                '[{"user_provided_doc_type":"SIGNED_SOW","user_provided_status":"signed"}]'
            ),
        },
        files=[
            ("target_file", ("draft.txt", io.BytesIO(DRAFT_SOW_TARGET_TEXT.encode()), "text/plain")),
            (
                "reference_files",
                ("signed.txt", io.BytesIO(SIGNED_SOW_TEXT.encode()), "text/plain"),
            ),
        ],
    )
    assert response.status_code == 200


def test_delete_runs_endpoints(client: TestClient) -> None:
    create = client.post("/analysis/lint")
    assert create.status_code == 200
    run_id = create.json()["analysis_run_id"]
    assert run_id is not None

    delete_one = client.delete(f"/analysis/runs/{run_id}")
    assert delete_one.status_code == 200
    assert client.get(f"/analysis/runs/{run_id}").status_code == 404

    client.post("/analysis/lint")
    clear_all = client.delete("/analysis/runs")
    assert clear_all.status_code == 200
    assert clear_all.json()["deleted"] >= 1
    assert client.get("/analysis/runs").json() == []


def test_custom_endpoint_accepts_profile_hints(client: TestClient) -> None:
    response = client.post(
        "/analysis/lint/custom",
        json={
            "project_id": "hints_test",
            "target": {
                "filename": "draft.txt",
                "text": DRAFT_SOW_TARGET_TEXT,
            },
            "target_doc_type": DocType.DRAFT_SOW.value,
            "references": [
                {
                    "filename": "signed.txt",
                    "text": SIGNED_SOW_TEXT,
                    "profile_hints": {
                        "user_provided_doc_type": DocType.SIGNED_SOW.value,
                        "user_provided_origin": SourceOrigin.CLIENT.value,
                        "user_provided_status": SourceStatus.SIGNED.value,
                    },
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["correction_ui_response"]["project_id"] == "hints_test"


def test_upload_endpoint_accepts_text_files(client: TestClient) -> None:
    response = client.post(
        "/analysis/lint/upload",
        data={"target_doc_type": DocType.DRAFT_SOW.value},
        files=[
            ("target_file", ("draft.txt", io.BytesIO(DRAFT_SOW_TARGET_TEXT.encode()), "text/plain")),
            (
                "reference_files",
                ("signed.txt", io.BytesIO(SIGNED_SOW_TEXT.encode()), "text/plain"),
            ),
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["correction_ui_response"]["summary"]["total_findings"] >= 0
