"""Request models for user-provided document uploads."""

from datetime import date
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.enums import DocType, SourceOrigin, SourceStatus
from backend.app.schemas.source_profile import SourceProfileInput


class UploadedDocument(BaseModel):
    document_id: str | None = None
    filename: str
    text: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, value: str) -> str:
        if not value.strip():
            msg = "Document text cannot be empty"
            raise ValueError(msg)
        return value

    def resolved_id(self) -> str:
        return self.document_id or f"doc_{uuid4().hex[:12]}"


class ReferenceProfileHints(BaseModel):
    user_provided_doc_type: DocType | None = None
    user_provided_origin: SourceOrigin | None = None
    user_provided_status: SourceStatus | None = None
    user_provided_recency_date: date | None = None


class ReferenceUpload(UploadedDocument):
    profile_hints: ReferenceProfileHints | None = None
    profile_input: SourceProfileInput | None = None


def build_reference_profile_input(
    document_id: str,
    reference: ReferenceUpload,
) -> SourceProfileInput:
    if reference.profile_input is not None:
        if reference.profile_input.document_id != document_id:
            return reference.profile_input.model_copy(update={"document_id": document_id})
        return reference.profile_input

    if reference.profile_hints is not None:
        return SourceProfileInput(
            document_id=document_id,
            **reference.profile_hints.model_dump(exclude_none=True),
        )

    return SourceProfileInput(document_id=document_id)


class CustomLintRequest(BaseModel):
    project_id: str = Field(default_factory=lambda: f"project_{uuid4().hex[:8]}")
    target: UploadedDocument
    target_doc_type: DocType = DocType.DRAFT_SOW
    references: list[ReferenceUpload] = Field(default_factory=list)
