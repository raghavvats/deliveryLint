"""SQLite persistence for projects, references, and analysis runs."""

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from sqlalchemy import inspect
from sqlmodel import Field, Session, SQLModel, create_engine, select

from backend.app.config.settings import get_settings
from backend.app.schemas.analysis_run import AnalysisRunDetail, AnalysisRunStatus, AnalysisRunSummary, RunFindingsSummary
from backend.app.schemas.correction_ui import CorrectionUIResponse
from backend.app.schemas.project import ProjectDetail, ProjectSummary, ReferenceDocumentDetail, ReferenceDocumentSummary
from backend.app.schemas.project import ReferenceDocumentStatus
from backend.app.schemas.enums import DocType
from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.source_profile import SourceProfile


class ProjectRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReferenceDocumentRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    project_id: str = Field(foreign_key="projectrecord.id", index=True)
    filename: str
    text: str
    profile_document_id: str = ""
    profile_hints_json: str = "{}"
    cached_profile_json: str = ""
    cached_facts_json: str = "[]"
    status: str = ReferenceDocumentStatus.READY.value
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnalysisRunRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: str = Field(index=True)
    name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = AnalysisRunStatus.COMPLETED.value
    error_message: str | None = None
    response_json: str | None = None


def ensure_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _migrate_schema(engine) -> None:
    if not inspect(engine).has_table("analysisrunrecord"):
        return
    columns = {column["name"] for column in inspect(engine).get_columns("analysisrunrecord")}
    with engine.begin() as connection:
        if "name" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE analysisrunrecord ADD COLUMN name VARCHAR NOT NULL DEFAULT ''"
            )
        if "status" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE analysisrunrecord ADD COLUMN status VARCHAR NOT NULL DEFAULT 'completed'"
            )
        if "error_message" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE analysisrunrecord ADD COLUMN error_message VARCHAR"
            )

    if not inspect(engine).has_table("referencedocumentrecord"):
        return
    ref_columns = {
        column["name"] for column in inspect(engine).get_columns("referencedocumentrecord")
    }
    with engine.begin() as connection:
        if "profile_document_id" not in ref_columns:
            connection.exec_driver_sql(
                "ALTER TABLE referencedocumentrecord ADD COLUMN profile_document_id VARCHAR NOT NULL DEFAULT ''"
            )
        if "status" not in ref_columns:
            connection.exec_driver_sql(
                "ALTER TABLE referencedocumentrecord ADD COLUMN status VARCHAR NOT NULL DEFAULT 'ready'"
            )
        if "error_message" not in ref_columns:
            connection.exec_driver_sql(
                "ALTER TABLE referencedocumentrecord ADD COLUMN error_message VARCHAR"
            )


def get_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, echo=False, connect_args=connect_args)


_init_lock = Lock()


def init_db(database_url: str | None = None) -> None:
    with _init_lock:
        engine = get_engine(database_url)
        SQLModel.metadata.create_all(engine)
        _migrate_schema(engine)


def _run_status(record: AnalysisRunRecord) -> AnalysisRunStatus:
    try:
        return AnalysisRunStatus(record.status)
    except ValueError:
        return AnalysisRunStatus.COMPLETED


def _findings_summary_from_record(record: AnalysisRunRecord) -> RunFindingsSummary | None:
    if _run_status(record) != AnalysisRunStatus.COMPLETED or not record.response_json:
        return None
    try:
        correction = CorrectionUIResponse.model_validate_json(record.response_json)
    except Exception:
        return None
    summary = correction.summary
    return RunFindingsSummary(
        total_findings=summary.total_findings,
        needs_fix_count=summary.needs_fix_count,
        needs_review_count=summary.needs_review_count,
        has_blocking_issues=summary.has_blocking_issues,
    )


def _to_run_summary(record: AnalysisRunRecord) -> AnalysisRunSummary:
    assert record.id is not None
    return AnalysisRunSummary(
        id=record.id,
        project_id=record.project_id,
        name=record.name,
        created_at=ensure_utc_datetime(record.created_at),
        status=_run_status(record),
        error_message=record.error_message,
        findings_summary=_findings_summary_from_record(record),
    )


# --- Projects ---


def create_project(name: str, *, database_url: str | None = None) -> ProjectRecord:
    init_db(database_url)
    engine = get_engine(database_url)
    record = ProjectRecord(id=f"project_{uuid4().hex[:8]}", name=name.strip())
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def get_project(project_id: str, *, database_url: str | None = None) -> ProjectRecord | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        return session.get(ProjectRecord, project_id)


def delete_project(project_id: str, *, database_url: str | None = None) -> bool:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        project = session.get(ProjectRecord, project_id)
        if project is None:
            return False
        refs = session.exec(
            select(ReferenceDocumentRecord).where(ReferenceDocumentRecord.project_id == project_id)
        ).all()
        for ref in refs:
            session.delete(ref)
        runs = session.exec(
            select(AnalysisRunRecord).where(AnalysisRunRecord.project_id == project_id)
        ).all()
        for run in runs:
            session.delete(run)
        session.delete(project)
        session.commit()
    return True


def list_projects(*, database_url: str | None = None) -> list[ProjectSummary]:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        projects = session.exec(select(ProjectRecord).order_by(ProjectRecord.created_at.desc())).all()
        summaries: list[ProjectSummary] = []
        for project in projects:
            ref_count = len(
                session.exec(
                    select(ReferenceDocumentRecord).where(
                        ReferenceDocumentRecord.project_id == project.id
                    )
                ).all()
            )
            runs = session.exec(
                select(AnalysisRunRecord).where(AnalysisRunRecord.project_id == project.id)
            ).all()
            processing = sum(1 for r in runs if r.status == AnalysisRunStatus.PROCESSING.value)
            summaries.append(
                ProjectSummary(
                    id=project.id,
                    name=project.name,
                    created_at=ensure_utc_datetime(project.created_at),
                    reference_count=ref_count,
                    target_count=len(runs),
                    processing_count=processing,
                )
            )
        return summaries


def get_project_detail(project_id: str, *, database_url: str | None = None) -> ProjectDetail | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        project = session.get(ProjectRecord, project_id)
        if project is None:
            return None
        refs = session.exec(
            select(ReferenceDocumentRecord)
            .where(ReferenceDocumentRecord.project_id == project_id)
            .order_by(ReferenceDocumentRecord.created_at)
        ).all()
        runs = session.exec(
            select(AnalysisRunRecord)
            .where(AnalysisRunRecord.project_id == project_id)
            .order_by(AnalysisRunRecord.created_at.desc())
        ).all()
        return ProjectDetail(
            id=project.id,
            name=project.name,
            created_at=ensure_utc_datetime(project.created_at),
            references=[_to_reference_summary(r) for r in refs],
            runs=[_to_run_summary(r) for r in runs if r.id is not None],
        )


def _reference_status(record: ReferenceDocumentRecord) -> ReferenceDocumentStatus:
    try:
        status = ReferenceDocumentStatus(record.status)
    except ValueError:
        status = ReferenceDocumentStatus.READY
    if status == ReferenceDocumentStatus.READY and not record.cached_profile_json:
        return ReferenceDocumentStatus.PROCESSING
    return status


def _to_reference_summary(record: ReferenceDocumentRecord) -> ReferenceDocumentSummary:
    status = _reference_status(record)
    if status == ReferenceDocumentStatus.READY and record.cached_profile_json:
        profile = SourceProfile.model_validate_json(record.cached_profile_json)
        doc_type = profile.doc_type
    else:
        doc_type = DocType.UNKNOWN
    return ReferenceDocumentSummary(
        id=record.id,
        project_id=record.project_id,
        filename=record.filename,
        doc_type=doc_type,
        created_at=ensure_utc_datetime(record.created_at),
        status=status,
        error_message=record.error_message,
    )


def create_pending_reference_record(
    *,
    project_id: str,
    filename: str,
    text: str,
    profile_document_id: str,
    profile_hints_json: str,
    database_url: str | None = None,
) -> ReferenceDocumentRecord:
    init_db(database_url)
    engine = get_engine(database_url)
    record = ReferenceDocumentRecord(
        id=f"ref_{uuid4().hex[:12]}",
        project_id=project_id,
        filename=filename,
        text=text,
        profile_document_id=profile_document_id,
        profile_hints_json=profile_hints_json,
        cached_profile_json="",
        cached_facts_json="[]",
        status=ReferenceDocumentStatus.PROCESSING.value,
    )
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def complete_reference_record(
    ref_id: str,
    *,
    cached_profile: SourceProfile,
    cached_facts: list[ProjectFact],
    database_url: str | None = None,
) -> ReferenceDocumentRecord | None:
    import json

    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(ReferenceDocumentRecord, ref_id)
        if record is None:
            return None
        record.cached_profile_json = cached_profile.model_dump_json()
        record.cached_facts_json = json.dumps([f.model_dump(mode="json") for f in cached_facts])
        record.profile_document_id = cached_profile.document_id
        record.status = ReferenceDocumentStatus.READY.value
        record.error_message = None
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def fail_reference_record(
    ref_id: str,
    error_message: str,
    *,
    database_url: str | None = None,
) -> ReferenceDocumentRecord | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(ReferenceDocumentRecord, ref_id)
        if record is None:
            return None
        record.status = ReferenceDocumentStatus.FAILED.value
        record.error_message = error_message
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def save_reference_document(
    *,
    project_id: str,
    filename: str,
    text: str,
    profile_hints_json: str,
    cached_profile: SourceProfile,
    cached_facts: list[ProjectFact],
    database_url: str | None = None,
) -> ReferenceDocumentRecord:
    import json

    init_db(database_url)
    engine = get_engine(database_url)
    record = ReferenceDocumentRecord(
        id=f"ref_{uuid4().hex[:12]}",
        project_id=project_id,
        filename=filename,
        text=text,
        profile_document_id=cached_profile.document_id,
        profile_hints_json=profile_hints_json,
        cached_profile_json=cached_profile.model_dump_json(),
        cached_facts_json=json.dumps([f.model_dump(mode="json") for f in cached_facts]),
        status=ReferenceDocumentStatus.READY.value,
    )
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def get_reference_document(
    project_id: str,
    ref_id: str,
    *,
    database_url: str | None = None,
) -> ReferenceDocumentDetail | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(ReferenceDocumentRecord, ref_id)
        if record is None or record.project_id != project_id:
            return None
        summary = _to_reference_summary(record)
        if summary.status != ReferenceDocumentStatus.READY:
            return None
        return ReferenceDocumentDetail(
            id=record.id,
            project_id=record.project_id,
            filename=record.filename,
            text=record.text,
            doc_type=summary.doc_type,
            created_at=summary.created_at,
            status=summary.status,
            error_message=summary.error_message,
        )


def list_reference_documents(
    project_id: str,
    *,
    database_url: str | None = None,
) -> list[ReferenceDocumentRecord]:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        return list(
            session.exec(
                select(ReferenceDocumentRecord)
                .where(ReferenceDocumentRecord.project_id == project_id)
                .order_by(ReferenceDocumentRecord.created_at)
            ).all()
        )


def list_ready_reference_documents(
    project_id: str,
    *,
    database_url: str | None = None,
) -> list[ReferenceDocumentRecord]:
    return [
        record
        for record in list_reference_documents(project_id, database_url=database_url)
        if _reference_status(record) == ReferenceDocumentStatus.READY and record.cached_profile_json
    ]


def delete_reference_document(
    project_id: str,
    ref_id: str,
    *,
    database_url: str | None = None,
) -> bool:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(ReferenceDocumentRecord, ref_id)
        if record is None or record.project_id != project_id:
            return False
        session.delete(record)
        session.commit()
    return True


def load_cached_reference_data(
    record: ReferenceDocumentRecord,
) -> tuple[SourceProfile, list[ProjectFact]]:
    import json

    if not record.cached_profile_json:
        msg = f"Reference {record.id} is not ready for linting"
        raise ValueError(msg)

    profile = SourceProfile.model_validate_json(record.cached_profile_json)
    facts_raw = json.loads(record.cached_facts_json or "[]")
    facts = [ProjectFact.model_validate(item) for item in facts_raw]
    return profile, facts


# --- Analysis runs ---


def save_analysis_run(
    project_id: str,
    response_json: str,
    *,
    name: str = "",
    status: AnalysisRunStatus = AnalysisRunStatus.COMPLETED,
    error_message: str | None = None,
    database_url: str | None = None,
) -> AnalysisRunRecord:
    init_db(database_url)
    engine = get_engine(database_url)
    record = AnalysisRunRecord(
        project_id=project_id,
        name=name,
        response_json=response_json,
        status=status.value,
        error_message=error_message,
    )
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def create_processing_run(
    project_id: str,
    *,
    name: str = "",
    database_url: str | None = None,
) -> AnalysisRunRecord:
    init_db(database_url)
    engine = get_engine(database_url)
    record = AnalysisRunRecord(
        project_id=project_id,
        name=name,
        status=AnalysisRunStatus.PROCESSING.value,
        response_json="",
    )
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def complete_analysis_run(
    run_id: int,
    response_json: str,
    *,
    name: str | None = None,
    database_url: str | None = None,
) -> AnalysisRunRecord | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(AnalysisRunRecord, run_id)
        if record is None:
            return None
        record.status = AnalysisRunStatus.COMPLETED.value
        record.response_json = response_json
        record.error_message = None
        if name is not None:
            record.name = name
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def fail_analysis_run(
    run_id: int,
    error_message: str,
    *,
    database_url: str | None = None,
) -> AnalysisRunRecord | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(AnalysisRunRecord, run_id)
        if record is None:
            return None
        record.status = AnalysisRunStatus.FAILED.value
        record.error_message = error_message
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def mark_analysis_run_processing(
    run_id: int,
    *,
    database_url: str | None = None,
) -> AnalysisRunRecord | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(AnalysisRunRecord, run_id)
        if record is None:
            return None
        record.status = AnalysisRunStatus.PROCESSING.value
        record.error_message = None
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def get_analysis_run_record(
    run_id: int,
    *,
    database_url: str | None = None,
) -> AnalysisRunRecord | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        return session.get(AnalysisRunRecord, run_id)


def list_completed_run_records(
    project_id: str,
    *,
    database_url: str | None = None,
) -> list[AnalysisRunRecord]:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        records = session.exec(
            select(AnalysisRunRecord)
            .where(AnalysisRunRecord.project_id == project_id)
            .where(AnalysisRunRecord.status == AnalysisRunStatus.COMPLETED.value)
            .order_by(AnalysisRunRecord.created_at.desc())
        ).all()
    return [record for record in records if record.id is not None and record.response_json]


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
        _to_run_summary(record)
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
    correction = None
    if record.response_json:
        correction = CorrectionUIResponse.model_validate_json(record.response_json)
    return AnalysisRunDetail(
        id=record.id,
        project_id=record.project_id,
        name=record.name,
        created_at=ensure_utc_datetime(record.created_at),
        status=_run_status(record),
        error_message=record.error_message,
        correction_ui_response=correction,
    )


def update_analysis_run_name(
    run_id: int,
    name: str,
    database_url: str | None = None,
) -> AnalysisRunSummary | None:
    init_db(database_url)
    engine = get_engine(database_url)
    with Session(engine) as session:
        record = session.get(AnalysisRunRecord, run_id)
        if record is None or record.id is None:
            return None
        record.name = name
        session.add(record)
        session.commit()
        session.refresh(record)
        return _to_run_summary(record)
