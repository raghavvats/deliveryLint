from backend.app.config.document_content_config import (
    DEFAULT_EXPECTED_CONTENT_BY_DOC_TYPE,
    is_target_eligible_doc_type,
)
from backend.app.domain.authority import build_authority_rationale, compute_authority_level
from backend.app.domain.content import compute_missing_expected_content
from backend.app.domain.normalization import fallback_normalized_subject
from backend.app.schemas.enums import DocType, FactCategory, SourceOrigin, SourceStatus


def test_compute_missing_expected_content() -> None:
    expected = [FactCategory.SCOPE, FactCategory.OUT_OF_SCOPE, FactCategory.DATES]
    observed = [FactCategory.SCOPE]
    missing = compute_missing_expected_content(expected, observed)
    assert missing == [FactCategory.OUT_OF_SCOPE, FactCategory.DATES]


def test_fallback_normalized_subject() -> None:
    assert fallback_normalized_subject("NetSuite Billing Sync") == "netsuite_billing_sync"
    assert fallback_normalized_subject("  ") == "unknown_subject"


def test_compute_authority_level_signed_sow() -> None:
    level = compute_authority_level(
        DocType.SIGNED_SOW,
        origin=SourceOrigin.JOINT,
        status=SourceStatus.SIGNED,
        reliability_flags=[],
    )
    assert level == 5


def test_is_target_eligible_unknown() -> None:
    assert is_target_eligible_doc_type(DocType.UNKNOWN) is False


def test_all_doc_types_have_expected_content_entry() -> None:
    for doc_type in DocType:
        assert doc_type in DEFAULT_EXPECTED_CONTENT_BY_DOC_TYPE


def test_authority_rationale() -> None:
    rationale = build_authority_rationale(DocType.SIGNED_SOW, SourceStatus.SIGNED, 5)
    assert "high-authority" in rationale
