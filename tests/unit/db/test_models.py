import pytest

pytest.importorskip("sqlmodel")

from backend.app.db.models import get_analysis_run, list_analysis_runs, save_analysis_run


def test_save_and_list_analysis_runs(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    save_analysis_run("project_001", '{"project_id":"project_001"}', database_url=url)
    save_analysis_run("project_002", '{"project_id":"project_002"}', database_url=url)

    all_runs = list_analysis_runs(database_url=url)
    assert len(all_runs) == 2
    assert all_runs[0].project_id == "project_002"

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
    record = save_analysis_run("project_001", response.model_dump_json(), database_url=url)
    detail = get_analysis_run(record.id, database_url=url)
    assert detail is not None
    assert detail.project_id == "project_001"
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
