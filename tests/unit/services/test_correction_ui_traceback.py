import asyncio

import pytest

from backend.app.schemas.correction_ui import CorrectionTargetDocument
from backend.app.schemas.enums import DocType, InferenceSource, LintFindingType, LintSeverity
from backend.app.schemas.lint import LintFinding, RunLintOutput
from backend.app.schemas.project_fact import EvidenceSpan, ProjectFact
from backend.app.schemas.source_profile import SourceProfile
from backend.app.schemas.target_document import TargetLocation, TargetProfile
from backend.app.schemas.target_parser import TargetParseResult
from backend.app.services.correction_ui import build_correction_ui_response_from_parts


def _minimal_target_parse(document_id: str = "target_1") -> TargetParseResult:
    return TargetParseResult(
        target_profile=TargetProfile(
            document_id=document_id,
            doc_type=DocType.DRAFT_SOW,
            doc_type_confidence=1.0,
            doc_type_source=InferenceSource.USER,
            expected_content=[],
            observed_content=[],
            missing_expected_content=[],
            target_rubric_id="draft_sow",
            quality_flags=[],
        ),
        sections=[],
        claims=[],
        warnings=[],
    )


def test_builds_reference_evidence_from_related_fact_ids() -> None:
    profile = SourceProfile.model_validate(
        {
            "id": "profile_1",
            "document_id": "ref_1",
            "doc_type": "SIGNED_SOW",
            "doc_type_confidence": 1.0,
            "doc_type_source": "user",
            "origin": "client",
            "origin_confidence": 1.0,
            "origin_source": "user",
            "status": "signed",
            "status_confidence": 1.0,
            "status_source": "user",
            "authority_level": 5,
            "authority_rationale": "signed sow",
            "expected_content": [],
            "observed_content": [],
            "missing_expected_content": [],
            "reliability_flags": [],
            "summary": "Signed SOW",
        }
    )
    fact = ProjectFact.model_validate(
        {
            "id": "fact_1",
            "project_id": "project_1",
            "document_id": "ref_1",
            "source_profile_id": "profile_1",
            "fact_type": "date",
            "text": "August 1, 2026",
            "subject": "go-live date",
            "normalized_subject": "go live date",
            "polarity": "positive",
            "fact_status": "signed",
            "evidence": {"quote": "August 1, 2026"},
            "source_authority_level": 5,
            "source_doc_type": "SIGNED_SOW",
            "source_status": "signed",
            "extraction_confidence": 0.95,
        }
    )
    finding = LintFinding(
        id="finding_1",
        project_id="project_1",
        target_document_id="target_1",
        finding_type=LintFindingType.REFERENCE_CONTRADICTION,
        severity=LintSeverity.HIGH,
        confidence=0.9,
        title="Date conflict",
        message="Dates disagree",
        target_location=TargetLocation(quote="September 1, 2026"),
        related_fact_ids=["fact_1"],
        related_source_profile_ids=["profile_1"],
        target_quote="September 1, 2026",
        reference_quotes=["August 1, 2026"],
        rule_id="contradiction.date_conflict",
    )

    response = build_correction_ui_response_from_parts(
        project_id="project_1",
        target_document=CorrectionTargetDocument(
            id="target_1",
            project_id="project_1",
            filename="draft.txt",
            text="Go-live is September 1, 2026.",
            doc_type=DocType.DRAFT_SOW,
        ),
        target_parse_result=_minimal_target_parse(),
        lint_output=RunLintOutput(findings=[finding], warnings=[]),
        source_profiles=[profile],
        project_facts=[fact],
        reference_text_by_document_id={"ref_1": "Official go-live: August 1, 2026."},
        reference_filenames_by_document_id={"ref_1": "signed_sow.txt"},
    )

    assert len(response.reference_documents) == 1
    assert response.reference_documents[0].filename == "signed_sow.txt"
    assert len(response.findings[0].reference_evidence) == 1
    assert response.findings[0].reference_evidence[0].quote == "August 1, 2026"
    assert response.findings[0].target_location is not None
    assert response.findings[0].target_location.char_start is not None


def test_builds_reference_evidence_from_reference_quotes_when_fact_ids_missing() -> None:
    profile = SourceProfile.model_validate(
        {
            "id": "profile_1",
            "document_id": "ref_1",
            "doc_type": "SIGNED_SOW",
            "doc_type_confidence": 1.0,
            "doc_type_source": "user",
            "origin": "client",
            "origin_confidence": 1.0,
            "origin_source": "user",
            "status": "signed",
            "status_confidence": 1.0,
            "status_source": "user",
            "authority_level": 5,
            "authority_rationale": "signed sow",
            "expected_content": [],
            "observed_content": [],
            "missing_expected_content": [],
            "reliability_flags": [],
            "summary": "Signed SOW",
        }
    )
    fact = ProjectFact.model_validate(
        {
            "id": "fact_1",
            "project_id": "project_1",
            "document_id": "ref_1",
            "source_profile_id": "profile_1",
            "fact_type": "date",
            "text": "August 1, 2026",
            "subject": "go-live date",
            "normalized_subject": "go live date",
            "polarity": "positive",
            "fact_status": "signed",
            "evidence": {"quote": "August 1, 2026"},
            "source_authority_level": 5,
            "source_doc_type": "SIGNED_SOW",
            "source_status": "signed",
            "extraction_confidence": 0.95,
        }
    )
    finding = LintFinding(
        id="finding_1",
        project_id="project_1",
        target_document_id="target_1",
        finding_type=LintFindingType.REFERENCE_CONTRADICTION,
        severity=LintSeverity.HIGH,
        confidence=0.9,
        title="Date conflict",
        message="Dates disagree",
        target_location=TargetLocation(quote="September 1, 2026"),
        related_fact_ids=[],
        reference_quotes=["August 1, 2026"],
        rule_id="contradiction.date_conflict",
    )

    response = build_correction_ui_response_from_parts(
        project_id="project_1",
        target_document=CorrectionTargetDocument(
            id="target_1",
            project_id="project_1",
            filename="draft.txt",
            text="Go-live is September 1, 2026.",
            doc_type=DocType.DRAFT_SOW,
        ),
        target_parse_result=_minimal_target_parse(),
        lint_output=RunLintOutput(findings=[finding], warnings=[]),
        source_profiles=[profile],
        project_facts=[fact],
        reference_text_by_document_id={"ref_1": "Official go-live: August 1, 2026."},
    )

    assert len(response.findings[0].reference_evidence) == 1
    assert response.findings[0].reference_evidence[0].fact_id == "fact_1"
