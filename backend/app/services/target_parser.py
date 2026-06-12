"""Target document parsing service."""

from uuid import uuid4

from backend.app.config.document_content_config import is_target_eligible_doc_type
from backend.app.config.target_document_config import (
    MIN_TARGET_CLAIM_CONFIDENCE,
    TARGET_DOCUMENT_CONFIG_BY_DOC_TYPE,
    TargetDocumentConfig,
)
from backend.app.domain.content import compute_missing_expected_content
from backend.app.domain.normalization import fallback_normalized_subject
from backend.app.schemas.enums import DocType, InferenceSource, TargetQualityFlag
from backend.app.schemas.target_document import TargetClaim, TargetProfile, TargetSection
from backend.app.schemas.target_parser import (
    ParseTargetDocumentInput,
    TargetDocumentLLMResponse,
    TargetParseResult,
    TargetParseWarning,
    TargetParseWarningCode,
)
from backend.app.services.llm_client import LLMClient, get_default_llm_client


def validate_and_enrich_target_parse(
    *,
    project_id: str,
    document_id: str,
    target_doc_type: DocType,
    target_doc_type_source: InferenceSource,
    target_doc_type_confidence: float,
    config: TargetDocumentConfig,
    llm_response: TargetDocumentLLMResponse,
) -> TargetParseResult:
    warnings: list[TargetParseWarning] = list(llm_response.warnings)
    quality_flags: list[TargetQualityFlag] = []

    if not is_target_eligible_doc_type(target_doc_type):
        return TargetParseResult(
            target_profile=TargetProfile(
                document_id=document_id,
                doc_type=target_doc_type,
                doc_type_confidence=target_doc_type_confidence,
                doc_type_source=target_doc_type_source,
                expected_content=[],
                observed_content=[],
                missing_expected_content=[],
                target_rubric_id="none",
                quality_flags=[TargetQualityFlag.TARGET_TYPE_NOT_ELIGIBLE],
            ),
            sections=[],
            claims=[],
            warnings=[
                TargetParseWarning(
                    code=TargetParseWarningCode.TARGET_TYPE_NOT_ELIGIBLE,
                    message=(
                        f"{target_doc_type.value} is not eligible as a target document type."
                    ),
                )
            ],
        )

    expected_content = config.expected_content
    observed_content = llm_response.observed_content
    missing_expected_content = compute_missing_expected_content(
        expected_content=expected_content,
        observed_content=observed_content,
    )

    if missing_expected_content:
        quality_flags.append(TargetQualityFlag.MISSING_EXPECTED_CONTENT)
        for category in missing_expected_content:
            warnings.append(
                TargetParseWarning(
                    code=TargetParseWarningCode.MISSING_EXPECTED_CONTENT,
                    message=(
                        f"Target document appears to be missing expected content: "
                        f"{category.value}."
                    ),
                    related_content_category=category,
                )
            )

    sections: list[TargetSection] = []
    for section in llm_response.sections:
        sections.append(
            TargetSection(
                id=f"section_{uuid4().hex}",
                document_id=document_id,
                title=section.title,
                normalized_title=section.normalized_title
                or fallback_normalized_subject(section.title),
                text=section.text,
                content_categories=section.content_categories,
                location=section.location,
            )
        )

    if not sections:
        quality_flags.append(TargetQualityFlag.UNSTRUCTURED_DOCUMENT)
        quality_flags.append(TargetQualityFlag.MISSING_SECTION_HEADINGS)
        warnings.append(
            TargetParseWarning(
                code=TargetParseWarningCode.NO_SECTIONS_DETECTED,
                message="No target document sections were detected.",
            )
        )

    claims: list[TargetClaim] = []
    for candidate in llm_response.claims:
        if candidate.claim_type not in config.target_claim_types:
            warnings.append(
                TargetParseWarning(
                    code=TargetParseWarningCode.UNSUPPORTED_CLAIM_DROPPED,
                    message=(
                        f"Dropped claim of type {candidate.claim_type.value} because "
                        "it is not allowed for this target document type."
                    ),
                    related_claim_type=candidate.claim_type,
                )
            )
            continue

        if candidate.checkable and (
            candidate.location is None
            or candidate.location.quote is None
            or not candidate.location.quote.strip()
        ):
            warnings.append(
                TargetParseWarning(
                    code=TargetParseWarningCode.TARGET_LOCATION_MISSING,
                    message=(
                        "Dropped checkable target claim because it had no target quote."
                    ),
                    related_claim_type=candidate.claim_type,
                )
            )
            continue

        if candidate.extraction_confidence < MIN_TARGET_CLAIM_CONFIDENCE:
            warnings.append(
                TargetParseWarning(
                    code=TargetParseWarningCode.LOW_CONFIDENCE_EXTRACTION,
                    message=(
                        f"Dropped low-confidence target claim with confidence "
                        f"{candidate.extraction_confidence:.2f}."
                    ),
                    related_claim_type=candidate.claim_type,
                )
            )
            continue

        normalized_subject = candidate.normalized_subject.strip()
        if not normalized_subject:
            normalized_subject = fallback_normalized_subject(candidate.subject)

        claims.append(
            TargetClaim(
                id=f"claim_{uuid4().hex}",
                project_id=project_id,
                document_id=document_id,
                claim_type=candidate.claim_type,
                text=candidate.text,
                subject=candidate.subject,
                normalized_subject=normalized_subject,
                polarity=candidate.polarity,
                claim_status=candidate.claim_status,
                attributes=candidate.attributes,
                location=candidate.location,
                checkable=candidate.checkable,
                non_checkable_reason=candidate.non_checkable_reason,
                extraction_confidence=candidate.extraction_confidence,
            )
        )

    if not claims:
        warnings.append(
            TargetParseWarning(
                code=TargetParseWarningCode.NO_CLAIMS_EXTRACTED,
                message="No valid target claims were extracted from this document.",
            )
        )

    quality_flags = list(dict.fromkeys(quality_flags))

    target_profile = TargetProfile(
        document_id=document_id,
        doc_type=target_doc_type,
        doc_type_confidence=target_doc_type_confidence,
        doc_type_source=target_doc_type_source,
        expected_content=expected_content,
        observed_content=observed_content,
        missing_expected_content=missing_expected_content,
        target_rubric_id=config.target_rubric_id,
        quality_flags=quality_flags,
    )

    return TargetParseResult(
        target_profile=target_profile,
        sections=sections,
        claims=claims,
        warnings=warnings,
    )


async def infer_target_parse(
    input: ParseTargetDocumentInput,
    config: TargetDocumentConfig,
    llm_client: LLMClient | None = None,
) -> TargetDocumentLLMResponse:
    client = llm_client or get_default_llm_client()
    return await client.infer_target_parse(input, config)


async def parse_target_document(
    input: ParseTargetDocumentInput,
    llm_client: LLMClient | None = None,
    llm_response: TargetDocumentLLMResponse | None = None,
) -> TargetParseResult:
    config = TARGET_DOCUMENT_CONFIG_BY_DOC_TYPE[input.target_doc_type]
    if llm_response is None:
        llm_response = await infer_target_parse(input, config, llm_client=llm_client)

    return validate_and_enrich_target_parse(
        project_id=input.project_id,
        document_id=input.document.id,
        target_doc_type=input.target_doc_type,
        target_doc_type_source=input.target_doc_type_source,
        target_doc_type_confidence=input.target_doc_type_confidence,
        config=config,
        llm_response=llm_response,
    )
