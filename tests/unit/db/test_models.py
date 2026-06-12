import pytest

pytest.importorskip("sqlmodel")

from backend.app.db.models import init_db, save_analysis_run


def test_save_analysis_run(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    init_db(url)
    record = save_analysis_run("project_001", '{"ok": true}', database_url=url)
    assert record.id is not None
    assert record.project_id == "project_001"
