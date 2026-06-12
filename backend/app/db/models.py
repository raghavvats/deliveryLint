"""Minimal SQLite persistence for analysis runs (Phase 7)."""

from datetime import datetime, timezone

from sqlmodel import Field, Session, SQLModel, create_engine


class AnalysisRunRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    response_json: str


def get_engine(database_url: str = "sqlite:///deliverylint.db"):
    return create_engine(database_url, echo=False)


def init_db(database_url: str = "sqlite:///deliverylint.db") -> None:
    engine = get_engine(database_url)
    SQLModel.metadata.create_all(engine)


def save_analysis_run(
    project_id: str,
    response_json: str,
    database_url: str = "sqlite:///deliverylint.db",
) -> AnalysisRunRecord:
    init_db(database_url)
    engine = get_engine(database_url)
    record = AnalysisRunRecord(project_id=project_id, response_json=response_json)
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
    return record
