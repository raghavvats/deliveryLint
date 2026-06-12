"""Source document profiling service."""

from uuid import uuid4

from backend.app.config.document_content_config import (
    DEFAULT_EXPECTED_CONTENT_BY_DOC_TYPE,
    FACT_CATEGORY_KEYWORDS,
    get_expected_content,
)
from backend.app.domain.authority import build_authority_rationale, compute_authority_level
from backend.app.domain.content import compute_missing_expected_content
from backend.app.schemas.enums import (
    DocType,
    FactCategory,
    InferenceSource,
    ReliabilityFlag,
    SourceOrigin,
    SourceStatus,
)
from backend.app.schemas.source_profile import (
    ProfileSourceArgs,
    SourceProfile,
    SourceProfileInference,
    SourceProfileInput,
)
from backend.app.services.llm_client import LLMClient, get_default_llm_client


def infer_observed_content_from_text(text: str) -> list[FactCategory]:
    lowered = text.lower()
    observed: list[FactCategory] = []
    for category, keywords in FACT_CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            observed.append(category)
    return observed


def merge_source_profile(
    *,
    document_id: str,
    user_input: SourceProfileInput | None,
    inference: SourceProfileInference,
) -> SourceProfile:
    reliability_flags = list(inference.reliability_flags)

    if user_input and user_input.user_provided_doc_type is not None:
        doc_type = user_input.user_provided_doc_type
        doc_type_confidence = 1.0
        doc_type_source = InferenceSource.USER
        if (
            inference.inferred_doc_type != doc_type
            and inference.doc_type_confidence >= 0.75
        ):
            reliability_flags.append(ReliabilityFlag.USER_LABEL_CONFLICTS_WITH_CONTENT)
    else:
        doc_type = inference.inferred_doc_type
        doc_type_confidence = inference.doc_type_confidence
        doc_type_source = InferenceSource.INFERRED

    if user_input and user_input.user_provided_origin is not None:
        origin = user_input.user_provided_origin
        origin_confidence = 1.0
        origin_source = InferenceSource.USER
        if inference.inferred_origin != origin and inference.origin_confidence >= 0.75:
            reliability_flags.append(ReliabilityFlag.USER_LABEL_CONFLICTS_WITH_CONTENT)
    else:
        origin = inference.inferred_origin
        origin_confidence = inference.origin_confidence
        origin_source = InferenceSource.INFERRED

    if user_input and user_input.user_provided_status is not None:
        status = user_input.user_provided_status
        status_confidence = 1.0
        status_source = InferenceSource.USER
        if inference.inferred_status != status and inference.status_confidence >= 0.75:
            reliability_flags.append(ReliabilityFlag.USER_LABEL_CONFLICTS_WITH_CONTENT)
    else:
        status = inference.inferred_status
        status_confidence = inference.status_confidence
        status_source = InferenceSource.INFERRED

    if user_input and user_input.user_provided_recency_date is not None:
        recency_date = user_input.user_provided_recency_date
        recency_date_confidence = 1.0
        recency_date_source = InferenceSource.USER
    else:
        recency_date = inference.inferred_recency_date
        recency_date_confidence = inference.recency_date_confidence
        recency_date_source = (
            InferenceSource.INFERRED if inference.inferred_recency_date else InferenceSource.UNKNOWN
        )

    expected_content = get_expected_content(doc_type)
    observed_content = inference.observed_content
    missing_expected_content = compute_missing_expected_content(
        expected_content=expected_content,
        observed_content=observed_content,
    )

    if missing_expected_content:
        reliability_flags.append(ReliabilityFlag.MISSING_EXPECTED_CONTENT)

    reliability_flags = list(dict.fromkeys(reliability_flags))

    authority_level = compute_authority_level(
        doc_type=doc_type,
        origin=origin,
        status=status,
        reliability_flags=reliability_flags,
    )

    authority_rationale = build_authority_rationale(
        doc_type=doc_type,
        status=status,
        authority_level=authority_level,
    )

    return SourceProfile(
        id=f"profile_{uuid4().hex}",
        document_id=document_id,
        doc_type=doc_type,
        doc_type_confidence=doc_type_confidence,
        doc_type_source=doc_type_source,
        origin=origin,
        origin_confidence=origin_confidence,
        origin_source=origin_source,
        status=status,
        status_confidence=status_confidence,
        status_source=status_source,
        authority_level=authority_level,
        authority_rationale=authority_rationale,
        recency_date=recency_date,
        recency_date_confidence=recency_date_confidence,
        recency_date_source=recency_date_source,
        expected_content=expected_content,
        observed_content=observed_content,
        missing_expected_content=missing_expected_content,
        reliability_flags=reliability_flags,
        summary=inference.summary,
    )


async def infer_source_profile(
    args: ProfileSourceArgs,
    llm_client: LLMClient | None = None,
) -> SourceProfileInference:
    client = llm_client or get_default_llm_client()
    return await client.infer_source_profile(args)


def build_mock_inference(args: ProfileSourceArgs) -> SourceProfileInference:
    """Deterministic inference for mock pipeline when LLM returns fixture-like defaults."""
    observed = infer_observed_content_from_text(args.document.text)
    return SourceProfileInference(
        inferred_doc_type=DocType.UNKNOWN,
        doc_type_confidence=0.5,
        inferred_origin=SourceOrigin.UNKNOWN,
        origin_confidence=0.5,
        inferred_status=SourceStatus.UNKNOWN,
        status_confidence=0.5,
        observed_content=observed or list(DEFAULT_EXPECTED_CONTENT_BY_DOC_TYPE[DocType.UNKNOWN]),
        reliability_flags=[],
        summary="Mock inferred profile.",
    )


async def profile_source(
    args: ProfileSourceArgs,
    llm_client: LLMClient | None = None,
    use_mock_inference: bool = False,
) -> SourceProfile:
    if use_mock_inference:
        inference = build_mock_inference(args)
    else:
        inference = await infer_source_profile(args, llm_client=llm_client)

    document_id = args.input.document_id if args.input else args.document.id
    return merge_source_profile(
        document_id=document_id,
        user_input=args.input,
        inference=inference,
    )
