"""Fact extraction and validation service."""

from uuid import uuid4

from backend.app.config.fact_extraction_config import (
    FACT_EXTRACTION_CONFIG_BY_DOC_TYPE,
    MIN_EXTRACTION_CONFIDENCE,
    FactExtractionConfig,
)
from backend.app.domain.normalization import fallback_normalized_subject
from backend.app.schemas.enums import DocType
from backend.app.schemas.fact_parser import (
    ExtractProjectFactsInput,
    ExtractProjectFactsOutput,
    FactExtractionWarning,
    FactExtractionWarningCode,
    ProjectFactLLMResponse,
)
from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.source_profile import SourceProfile
from backend.app.services.llm_client import LLMClient, get_default_llm_client


def validate_and_enrich_project_facts(
    *,
    project_id: str,
    document_id: str,
    source_profile: SourceProfile,
    config: FactExtractionConfig,
    llm_response: ProjectFactLLMResponse,
) -> ExtractProjectFactsOutput:
    facts: list[ProjectFact] = []
    warnings: list[FactExtractionWarning] = list(llm_response.warnings)

    if source_profile.doc_type == DocType.UNKNOWN:
        warnings.append(
            FactExtractionWarning(
                code=FactExtractionWarningCode.UNKNOWN_DOC_TYPE_EXTRACTION,
                message=(
                    "Extracted facts from an UNKNOWN document type. "
                    "Treat these facts cautiously."
                ),
            )
        )

    for candidate in llm_response.facts:
        if candidate.fact_type not in config.target_fact_types:
            warnings.append(
                FactExtractionWarning(
                    code=FactExtractionWarningCode.UNSUPPORTED_FACT_DROPPED,
                    message=(
                        f"Dropped fact of type {candidate.fact_type.value} because "
                        "it is not allowed for this document type."
                    ),
                    related_fact_type=candidate.fact_type,
                )
            )
            continue

        if not candidate.evidence or not candidate.evidence.quote.strip():
            warnings.append(
                FactExtractionWarning(
                    code=FactExtractionWarningCode.UNSUPPORTED_FACT_DROPPED,
                    message=(
                        "Dropped candidate fact because it had no supporting "
                        "evidence quote."
                    ),
                    related_fact_type=candidate.fact_type,
                )
            )
            continue

        if candidate.extraction_confidence < MIN_EXTRACTION_CONFIDENCE:
            warnings.append(
                FactExtractionWarning(
                    code=FactExtractionWarningCode.LOW_CONFIDENCE_EXTRACTION,
                    message=(
                        f"Dropped low-confidence fact with confidence "
                        f"{candidate.extraction_confidence:.2f}."
                    ),
                    related_fact_type=candidate.fact_type,
                )
            )
            continue

        normalized_subject = candidate.normalized_subject.strip()
        if not normalized_subject:
            normalized_subject = fallback_normalized_subject(candidate.subject)

        facts.append(
            ProjectFact(
                id=f"fact_{uuid4().hex}",
                project_id=project_id,
                document_id=document_id,
                source_profile_id=source_profile.id,
                fact_type=candidate.fact_type,
                text=candidate.text,
                subject=candidate.subject,
                normalized_subject=normalized_subject,
                polarity=candidate.polarity,
                fact_status=candidate.fact_status,
                attributes=candidate.attributes,
                evidence=candidate.evidence,
                source_authority_level=source_profile.authority_level,
                source_doc_type=source_profile.doc_type,
                source_status=source_profile.status,
                extraction_confidence=candidate.extraction_confidence,
            )
        )

    if not facts:
        warnings.append(
            FactExtractionWarning(
                code=FactExtractionWarningCode.NO_FACTS_EXTRACTED,
                message="No valid project facts were extracted from this document.",
            )
        )

    return ExtractProjectFactsOutput(facts=facts, warnings=warnings)


async def infer_project_facts(
    input: ExtractProjectFactsInput,
    config: FactExtractionConfig,
    llm_client: LLMClient | None = None,
) -> ProjectFactLLMResponse:
    client = llm_client or get_default_llm_client()
    return await client.infer_project_facts(input, config)


async def extract_project_facts(
    input: ExtractProjectFactsInput,
    llm_client: LLMClient | None = None,
    llm_response: ProjectFactLLMResponse | None = None,
) -> ExtractProjectFactsOutput:
    config = FACT_EXTRACTION_CONFIG_BY_DOC_TYPE[input.source_profile.doc_type]
    if llm_response is None:
        llm_response = await infer_project_facts(input, config, llm_client=llm_client)

    return validate_and_enrich_project_facts(
        project_id=input.project_id,
        document_id=input.document.id,
        source_profile=input.source_profile,
        config=config,
        llm_response=llm_response,
    )
