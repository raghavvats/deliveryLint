"""Tests for heuristic source profiling when user hints are present."""

from backend.app.schemas.enums import DocType, SourceStatus
from backend.app.schemas.source_profile import ProfileSourceArgs, ProfileSourceDocument, SourceProfileInput
from backend.app.services.source_profiler import build_inference_from_hints, can_skip_llm_profile


def test_can_skip_llm_profile_when_hints_complete() -> None:
    args = ProfileSourceArgs(
        document=ProfileSourceDocument(id="doc1", text="# Signed SOW\nScope here."),
        input=SourceProfileInput(
            document_id="doc1",
            user_provided_doc_type=DocType.SIGNED_SOW,
            user_provided_status=SourceStatus.SIGNED,
        ),
    )
    assert can_skip_llm_profile(args) is True


def test_build_inference_from_hints_uses_doc_type() -> None:
    args = ProfileSourceArgs(
        document=ProfileSourceDocument(id="doc1", text="# Signed SOW\nOut of scope: SAP."),
        input=SourceProfileInput(
            document_id="doc1",
            user_provided_doc_type=DocType.SIGNED_SOW,
            user_provided_status=SourceStatus.SIGNED,
        ),
    )
    inference = build_inference_from_hints(args)
    assert inference.inferred_doc_type == DocType.SIGNED_SOW
    assert inference.inferred_status == SourceStatus.SIGNED
