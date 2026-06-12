"""Structured mock pipeline outputs for E2E sample."""

from datetime import date

from backend.app.schemas.enums import (
    DocType,
    FactCategory,
    FactPolarity,
    FactStatus,
    FactType,
    InferenceSource,
    ReliabilityFlag,
    SourceOrigin,
    SourceStatus,
)
from backend.app.schemas.fact_parser import ProjectFactLLMOutput, ProjectFactLLMResponse
from backend.app.schemas.project_fact import EvidenceSpan
from backend.app.schemas.source_profile import SourceProfileInference
from backend.app.schemas.target_document import TargetLocation
from backend.app.schemas.target_parser import (
    TargetClaimLLMOutput,
    TargetDocumentLLMResponse,
    TargetSectionLLMOutput,
)
from backend.app.fixtures.sample_documents import (
    CLIENT_EMAIL_DOC_ID,
    DRAFT_SOW_TARGET_TEXT,
    SIGNED_SOW_DOC_ID,
    TARGET_DOC_ID,
)

MOCK_SOURCE_INFERENCES: dict[str, SourceProfileInference] = {
    SIGNED_SOW_DOC_ID: SourceProfileInference(
        inferred_doc_type=DocType.SIGNED_SOW,
        doc_type_confidence=0.98,
        inferred_origin=SourceOrigin.JOINT,
        origin_confidence=0.86,
        inferred_status=SourceStatus.SIGNED,
        status_confidence=0.95,
        inferred_recency_date=date(2026, 6, 1),
        recency_date_confidence=0.9,
        observed_content=[
            FactCategory.SCOPE,
            FactCategory.OUT_OF_SCOPE,
            FactCategory.DELIVERABLES,
            FactCategory.DATES,
            FactCategory.RESPONSIBILITIES,
            FactCategory.SYSTEMS,
        ],
        reliability_flags=[ReliabilityFlag.MISSING_EXPECTED_CONTENT],
        summary="Signed SOW defining core implementation scope and timeline.",
    ),
    CLIENT_EMAIL_DOC_ID: SourceProfileInference(
        inferred_doc_type=DocType.CLIENT_EMAIL,
        doc_type_confidence=0.92,
        inferred_origin=SourceOrigin.CLIENT,
        origin_confidence=0.9,
        inferred_status=SourceStatus.INFORMAL,
        status_confidence=0.88,
        observed_content=[FactCategory.CLIENT_REQUESTS, FactCategory.SYSTEMS],
        reliability_flags=[ReliabilityFlag.INFORMAL_SOURCE],
        summary="Client email requesting NetSuite billing sync before launch.",
    ),
}

MOCK_FACT_RESPONSES: dict[str, ProjectFactLLMResponse] = {
    SIGNED_SOW_DOC_ID: ProjectFactLLMResponse(
        facts=[
            ProjectFactLLMOutput(
                fact_type=FactType.OUT_OF_SCOPE_ITEM,
                text="NetSuite billing integration is excluded from project scope.",
                subject="NetSuite billing integration",
                normalized_subject="netsuite_billing_integration",
                polarity=FactPolarity.NEGATIVE,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="Out of scope: NetSuite billing integration and custom tax logic."
                ),
                extraction_confidence=0.97,
            )
        ]
    ),
    CLIENT_EMAIL_DOC_ID: ProjectFactLLMResponse(
        facts=[
            ProjectFactLLMOutput(
                fact_type=FactType.CLIENT_REQUEST,
                text="Client requested adding NetSuite billing sync before launch.",
                subject="NetSuite billing sync",
                normalized_subject="netsuite_billing_integration",
                polarity=FactPolarity.NEUTRAL,
                fact_status=FactStatus.REQUESTED,
                evidence=EvidenceSpan(
                    quote="Can we also add NetSuite billing sync before launch?"
                ),
                extraction_confidence=0.94,
            )
        ]
    ),
}

MOCK_TARGET_RESPONSES: dict[str, TargetDocumentLLMResponse] = {
    TARGET_DOC_ID: TargetDocumentLLMResponse(
        observed_content=[
            FactCategory.SCOPE,
            FactCategory.DELIVERABLES,
            FactCategory.DATES,
            FactCategory.SYSTEMS,
        ],
        sections=[
            TargetSectionLLMOutput(
                title="Scope of Work",
                normalized_title="scope",
                text="The implementation will include NetSuite billing integration before go-live.",
                content_categories=[FactCategory.SCOPE, FactCategory.SYSTEMS],
                location=TargetLocation(section_title="Scope of Work", char_start=0, char_end=200),
            )
        ],
        claims=[
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="NetSuite billing integration is included before go-live.",
                subject="NetSuite billing integration",
                normalized_subject="netsuite_billing_integration",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=TargetLocation(
                    quote="The implementation will include NetSuite billing integration before go-live.",
                    section_title="Scope of Work",
                    char_start=40,
                    char_end=115,
                ),
                checkable=True,
                extraction_confidence=0.95,
            ),
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="Custom ERP analytics dashboard is included in scope.",
                subject="ERP analytics dashboard",
                normalized_subject="erp_analytics_dashboard",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=TargetLocation(
                    quote="Custom ERP analytics dashboard is included in scope.",
                    section_title="Scope of Work",
                ),
                checkable=True,
                extraction_confidence=0.88,
            ),
            TargetClaimLLMOutput(
                claim_type=FactType.DELIVERABLE,
                text="Deliver a seamless and user-friendly reporting experience.",
                subject="reporting experience",
                normalized_subject="reporting_experience",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=TargetLocation(
                    quote="Deliver a seamless and user-friendly reporting experience.",
                    section_title="Deliverables",
                ),
                checkable=True,
                extraction_confidence=0.8,
            ),
        ],
    ),
}

TARGET_DOC_TYPE = DocType.DRAFT_SOW
TARGET_DOC_TYPE_SOURCE = InferenceSource.USER
