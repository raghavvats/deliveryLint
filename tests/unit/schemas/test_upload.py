from datetime import date

from backend.app.schemas.enums import DocType, SourceOrigin, SourceStatus
from backend.app.schemas.upload import (
    ReferenceProfileHints,
    ReferenceUpload,
    build_reference_profile_input,
)


def test_build_reference_profile_input_from_hints() -> None:
    reference = ReferenceUpload(
        filename="signed.txt",
        text="signed sow text",
        profile_hints=ReferenceProfileHints(
            user_provided_doc_type=DocType.SIGNED_SOW,
            user_provided_origin=SourceOrigin.CLIENT,
            user_provided_status=SourceStatus.SIGNED,
            user_provided_recency_date=date(2026, 1, 15),
        ),
    )
    profile_input = build_reference_profile_input("doc_123", reference)
    assert profile_input.document_id == "doc_123"
    assert profile_input.user_provided_doc_type == DocType.SIGNED_SOW
    assert profile_input.user_provided_status == SourceStatus.SIGNED
    assert profile_input.user_provided_recency_date == date(2026, 1, 15)
