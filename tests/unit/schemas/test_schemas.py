from datetime import date

import pytest
from pydantic import ValidationError

from backend.app.schemas.common import AuthorityLevel
from backend.app.schemas.enums import (
    DocType,
    FactCategory,
    FactPolarity,
    FactStatus,
    FactType,
    InferenceSource,
    LintFindingType,
    LintSeverity,
    ReviewPriority,
    SourceOrigin,
    SourceStatus,
)
from backend.app.schemas.project_fact import EvidenceSpan, ProjectFact, ProjectFactAttributes
from backend.app.schemas.source_profile import SourceProfile


def test_authority_level_bounds() -> None:
    with pytest.raises(ValidationError):
        SourceProfile(
            id="p1",
            document_id="d1",
            doc_type=DocType.SIGNED_SOW,
            doc_type_confidence=1.0,
            doc_type_source=InferenceSource.USER,
            origin=SourceOrigin.JOINT,
            origin_confidence=0.9,
            origin_source=InferenceSource.INFERRED,
            status=SourceStatus.SIGNED,
            status_confidence=1.0,
            status_source=InferenceSource.USER,
            authority_level=6,
            authority_rationale="test",
            expected_content=[FactCategory.SCOPE],
            observed_content=[FactCategory.SCOPE],
            missing_expected_content=[],
            reliability_flags=[],
            summary="test",
        )


def test_evidence_quote_required() -> None:
    with pytest.raises(ValidationError):
        EvidenceSpan(quote="")


def test_project_fact_minimal() -> None:
    fact = ProjectFact(
        id="f1",
        project_id="proj1",
        document_id="d1",
        source_profile_id="p1",
        fact_type=FactType.SCOPE_ITEM,
        text="Scope includes CPQ.",
        subject="CPQ",
        normalized_subject="cpq",
        polarity=FactPolarity.POSITIVE,
        fact_status=FactStatus.SIGNED,
        evidence=EvidenceSpan(quote="Scope includes CPQ."),
        source_authority_level=5,
        source_doc_type=DocType.SIGNED_SOW,
        source_status=SourceStatus.SIGNED,
        extraction_confidence=0.95,
    )
    assert fact.normalized_subject == "cpq"


def test_review_priority_values() -> None:
    assert ReviewPriority.NEEDS_FIX.value == "needs_fix"
    assert len(LintFindingType) == 11
    assert len(LintSeverity) == 4
