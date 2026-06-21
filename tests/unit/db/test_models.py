import pytest
from datetime import datetime

pytest.importorskip("sqlmodel")

from backend.app.db.models import (
    create_project,
    create_processing_run,
    complete_analysis_run,
    ensure_utc_datetime,
    get_analysis_run,
    list_analysis_runs,
    save_analysis_run,
    update_analysis_run_name,
)


def test_save_and_list_analysis_runs(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    save_analysis_run("project_001", '{"project_id":"project_001"}', database_url=url)
    save_analysis_run("project_002", '{"project_id":"project_002"}', database_url=url)

    all_runs = list_analysis_runs(database_url=url)
    assert len(all_runs) == 2
    assert all_runs[0].project_id == "project_002"
    assert all_runs[0].status.value == "completed"

    project_runs = list_analysis_runs("project_001", database_url=url)
    assert len(project_runs) == 1
    assert project_runs[0].project_id == "project_001"


def test_get_analysis_run_returns_parsed_response(tmp_path) -> None:
    from backend.app.schemas.correction_ui import (
        CorrectionSummary,
        CorrectionTargetDocument,
        CorrectionUIResponse,
    )
    from backend.app.schemas.enums import DocType, InferenceSource
    from backend.app.schemas.target_document import TargetProfile

    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    response = CorrectionUIResponse(
        project_id="project_001",
        target_document=CorrectionTargetDocument(
            id="t1",
            project_id="project_001",
            filename="draft.txt",
            text="hello",
            doc_type=DocType.DRAFT_SOW,
        ),
        target_profile=TargetProfile(
            document_id="t1",
            doc_type=DocType.DRAFT_SOW,
            doc_type_confidence=1.0,
            doc_type_source=InferenceSource.USER,
            expected_content=[],
            observed_content=[],
            missing_expected_content=[],
            target_rubric_id="draft_sow",
            quality_flags=[],
        ),
        findings=[],
        lint_warnings=[],
        summary=CorrectionSummary(
            total_findings=0,
            needs_fix_count=0,
            needs_review_count=0,
            quality_suggestion_count=0,
            info_count=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            has_blocking_issues=False,
        ),
    )
    record = save_analysis_run("project_001", response.model_dump_json(), name="Billing review", database_url=url)
    detail = get_analysis_run(record.id, database_url=url)
    assert detail is not None
    assert detail.project_id == "project_001"
    assert detail.name == "Billing review"
    assert detail.correction_ui_response.target_document.filename == "draft.txt"


def test_clear_and_delete_analysis_runs(tmp_path) -> None:
    from backend.app.db.models import clear_analysis_runs, delete_analysis_run

    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    first = save_analysis_run("project_001", '{"project_id":"project_001"}', database_url=url)
    save_analysis_run("project_002", '{"project_id":"project_002"}', database_url=url)

    assert delete_analysis_run(first.id, database_url=url) is True
    remaining = list_analysis_runs(database_url=url)
    assert len(remaining) == 1
    assert remaining[0].project_id == "project_002"

    save_analysis_run("project_003", '{"project_id":"project_003"}', database_url=url)
    save_analysis_run("project_004", '{"project_id":"project_004"}', database_url=url)
    assert clear_analysis_runs(database_url=url) == 3
    assert list_analysis_runs(database_url=url) == []


def test_get_analysis_run_missing(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    assert get_analysis_run(999, database_url=url) is None


def test_ensure_utc_datetime_treats_naive_as_utc() -> None:
    naive = datetime(2025, 6, 16, 12, 0, 0)
    aware = ensure_utc_datetime(naive)
    assert aware.tzinfo is not None
    assert aware.hour == 12


def test_update_analysis_run_name(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    record = save_analysis_run("project_001", '{"project_id":"project_001"}', name="Old name", database_url=url)
    updated = update_analysis_run_name(record.id, "New name", database_url=url)
    assert updated is not None
    assert updated.name == "New name"
    listed = list_analysis_runs(database_url=url)
    assert listed[0].name == "New name"


def test_create_processing_run_allows_legacy_not_null_response_json_column(tmp_path) -> None:
    """Older SQLite schemas require response_json to be non-null."""
    from sqlmodel import Session

    from backend.app.db.models import ProjectRecord, create_processing_run, get_engine, init_db

    db_path = tmp_path / "legacy.db"
    url = f"sqlite:///{db_path}"
    init_db(url)
    engine = get_engine(url)

    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS analysisrunrecord")
        connection.exec_driver_sql(
            """
            CREATE TABLE analysisrunrecord (
                id INTEGER PRIMARY KEY,
                project_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL DEFAULT '',
                created_at DATETIME NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'completed',
                error_message VARCHAR,
                response_json VARCHAR NOT NULL
            )
            """
        )

    with Session(engine) as session:
        session.add(ProjectRecord(id="project_legacy", name="Legacy"))
        session.commit()

    record = create_processing_run("project_legacy", name="draft.txt", database_url=url)
    assert record.id is not None
    assert record.response_json == ""


def test_create_project_and_processing_run(tmp_path) -> None:
    from backend.app.schemas.correction_ui import (
        CorrectionSummary,
        CorrectionTargetDocument,
        CorrectionUIResponse,
    )
    from backend.app.schemas.enums import DocType, InferenceSource
    from backend.app.schemas.target_document import TargetProfile

    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    project = create_project("Acme rollout", database_url=url)
    assert project.id.startswith("project_")

    processing = create_processing_run(project.id, name="draft.txt", database_url=url)
    assert processing.status == "processing"
    assert processing.response_json == ""

    response = CorrectionUIResponse(
        project_id=project.id,
        target_document=CorrectionTargetDocument(
            id="t1",
            project_id=project.id,
            filename="draft.txt",
            text="hello",
            doc_type=DocType.DRAFT_SOW,
        ),
        target_profile=TargetProfile(
            document_id="t1",
            doc_type=DocType.DRAFT_SOW,
            doc_type_confidence=1.0,
            doc_type_source=InferenceSource.USER,
            expected_content=[],
            observed_content=[],
            missing_expected_content=[],
            target_rubric_id="draft_sow",
            quality_flags=[],
        ),
        findings=[],
        lint_warnings=[],
        summary=CorrectionSummary(
            total_findings=0,
            needs_fix_count=0,
            needs_review_count=0,
            quality_suggestion_count=0,
            info_count=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            has_blocking_issues=False,
        ),
    )
    complete_analysis_run(
        processing.id,
        response.model_dump_json(),
        name="draft.txt",
        database_url=url,
    )
    detail = get_analysis_run(processing.id, database_url=url)
    assert detail is not None
    assert detail.status.value == "completed"
    assert detail.correction_ui_response is not None
