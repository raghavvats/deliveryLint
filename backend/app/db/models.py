"""SQLite persistence for analysis runs (Phase 7)."""

from datetime import UTC, datetime

from sqlmodel import Field, Session, SQLModel, create_engine, select

from backend.app.config.settings import get_settings
from backend.app.schemas.analysis_run import AnalysisRunDetail, AnalysisRunSummary
from backend.app.schemas.correction_ui import CorrectionUIResponse


class AnalysisRunRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    response_json: str


def get_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, echo=False, connect_args=connect_args)


def init_db(database_url: str | None = None) -> None:
    engine = get_engine(database_url)
    SQLModel.metadata.create_all(engine)


def save_analysis_run(
    project_id: str,
    response_json: str,
    database_url: str | None = None,
) -> AnalysisRunRecord:
    init_db(database_url)
    engine = get_engine(database_url)
    record = AnalysisRunRecord(project_id=project_id, response_json=response_json)
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def list_analysis_runs(
    project_id: str | None = None,
    *,
    limit: int = 50,
    database_url: str | None = None,
) -> list[AnalysisRunSummary]:
    init_db(database_url)
    engine = get_engine(database_url)
    statement = select(AnalysisRunRecord).order_by(AnalysisRunRecord.created_at.desc()).limit(limit)
    if project_id is not None:
        statement = statement.where(AnalysisRunRecord.project_id == project_id)
    with Session(engine) as session:
        records = session.exec(statement).all()
    return [
        AnalysisRunSummary(id=record.id, project_id=record.project_id, created_at=record.created_at)
        for record in records
        if record.id is not None
    ]


def delete_analysis_run(
    run_id: int,
    database_url: str | None = None,
) -> bool:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(AnalysisRunRecord, run_id)
        if record is None:
            return False
        session.delete(record)
        session.commit()
    return True


def clear_analysis_runs(database_url: str | None = None) -> int:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        records = session.exec(select(AnalysisRunRecord)).all()
        for record in records:
            session.delete(record)
        session.commit()
    return len(records)


def get_analysis_run(
    run_id: int,
    database_url: str | None = None,
) -> AnalysisRunDetail | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(AnalysisRunRecord, run_id)
    if record is None or record.id is None:
        return None
    return AnalysisRunDetail(
        id=record.id,
        project_id=record.project_id,
        created_at=record.created_at,
        correction_ui_response=CorrectionUIResponse.model_validate_json(record.response_json),
    )
