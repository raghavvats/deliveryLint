"""Full in-memory pipeline orchestration."""

from backend.app.fixtures.mock_pipeline_outputs import (
    MOCK_FACT_RESPONSES,
    MOCK_SOURCE_INFERENCES,
    MOCK_TARGET_RESPONSES,
)
from backend.app.fixtures.sample_documents import (
    CLIENT_EMAIL_DOC_ID,
    CLIENT_EMAIL_TEXT,
    DRAFT_SOW_TARGET_TEXT,
    PROJECT_ID,
    SIGNED_SOW_DOC_ID,
    SIGNED_SOW_TEXT,
    TARGET_DOC_ID,
)
from backend.app.schemas.correction_ui import CorrectionTargetDocument
from backend.app.schemas.enums import DocType, InferenceSource, SourceOrigin, SourceStatus
from backend.app.schemas.fact_parser import ExtractProjectFactsInput, FactParserDocument
from backend.app.schemas.pipeline import PipelineDebugContext, PipelineResult
from backend.app.schemas.source_profile import (
    ProfileSourceArgs,
    ProfileSourceDocument,
    SourceProfileInput,
)
from backend.app.schemas.target_parser import ParseTargetDocumentInput, TargetParserDocument
from backend.app.services.correction_ui import build_correction_ui_response_from_parts
from backend.app.services.fact_clusterer import cluster_facts
from backend.app.services.fact_parser import extract_project_facts
from backend.app.services.llm_client import MockLLMClient, set_default_llm_client
from backend.app.services.lint_engine.run_lint import run_lint
from backend.app.services.source_profiler import profile_source
from backend.app.services.target_parser import parse_target_document
from backend.app.schemas.lint import RunLintInput


async def run_reference_document_pipeline(
    project_id: str,
    document_id: str,
    text: str,
    filename: str | None,
    profile_input: SourceProfileInput | None = None,
    llm_client: MockLLMClient | None = None,
):
    args = ProfileSourceArgs(
        document=ProfileSourceDocument(id=document_id, text=text, filename=filename),
        input=profile_input,
    )
    profile = await profile_source(args, llm_client=llm_client)
    fact_input = ExtractProjectFactsInput(
        project_id=project_id,
        document=FactParserDocument(id=document_id, text=text, filename=filename),
        source_profile=profile,
    )
    extract_output = await extract_project_facts(fact_input, llm_client=llm_client)
    clusters = cluster_facts(extract_output.facts)
    return profile, extract_output, clusters


async def run_target_document_pipeline(
    project_id: str,
    document_id: str,
    text: str,
    filename: str | None,
    target_doc_type: DocType,
    target_doc_type_source: InferenceSource = InferenceSource.USER,
    target_doc_type_confidence: float = 1.0,
    llm_client: MockLLMClient | None = None,
):
    parse_input = ParseTargetDocumentInput(
        project_id=project_id,
        document=TargetParserDocument(id=document_id, text=text, filename=filename),
        target_doc_type=target_doc_type,
        target_doc_type_source=target_doc_type_source,
        target_doc_type_confidence=target_doc_type_confidence,
    )
    return await parse_target_document(parse_input, llm_client=llm_client)


async def run_full_pipeline(
    project_id: str = PROJECT_ID,
    include_debug: bool = False,
) -> PipelineResult:
    llm_client = MockLLMClient(
        source_inferences=MOCK_SOURCE_INFERENCES,
        fact_responses=MOCK_FACT_RESPONSES,
        target_responses=MOCK_TARGET_RESPONSES,
    )
    set_default_llm_client(llm_client)

    signed_profile, signed_extract, _ = await run_reference_document_pipeline(
        project_id=project_id,
        document_id=SIGNED_SOW_DOC_ID,
        text=SIGNED_SOW_TEXT,
        filename="signed_sow.txt",
        profile_input=SourceProfileInput(
            document_id=SIGNED_SOW_DOC_ID,
            user_provided_doc_type=DocType.SIGNED_SOW,
            user_provided_status=SourceStatus.SIGNED,
        ),
        llm_client=llm_client,
    )

    email_profile, email_extract, _ = await run_reference_document_pipeline(
        project_id=project_id,
        document_id=CLIENT_EMAIL_DOC_ID,
        text=CLIENT_EMAIL_TEXT,
        filename="client_email.txt",
        llm_client=llm_client,
    )

    all_facts = signed_extract.facts + email_extract.facts
    all_profiles = [signed_profile, email_profile]
    all_clusters = cluster_facts(all_facts)

    target_parse = await run_target_document_pipeline(
        project_id=project_id,
        document_id=TARGET_DOC_ID,
        text=DRAFT_SOW_TARGET_TEXT,
        filename="draft_sow.txt",
        target_doc_type=DocType.DRAFT_SOW,
        llm_client=llm_client,
    )

    lint_output = run_lint(
        RunLintInput(
            project_id=project_id,
            target_parse_result=target_parse,
            source_profiles=all_profiles,
            project_facts=all_facts,
            fact_clusters=all_clusters,
        )
    )

    correction_response = build_correction_ui_response_from_parts(
        project_id=project_id,
        target_document=CorrectionTargetDocument(
            id=TARGET_DOC_ID,
            project_id=project_id,
            filename="draft_sow.txt",
            text=DRAFT_SOW_TARGET_TEXT,
            doc_type=DocType.DRAFT_SOW,
        ),
        target_parse_result=target_parse,
        lint_output=lint_output,
        source_profiles=all_profiles,
    )

    debug = None
    if include_debug:
        debug = PipelineDebugContext(
            source_profiles=all_profiles,
            extract_outputs=[signed_extract, email_extract],
            project_facts=all_facts,
            fact_clusters=all_clusters,
            target_parse_result=target_parse,
            run_lint_output=lint_output,
        )

    return PipelineResult(
        correction_ui_response=correction_response,
        run_lint_output=lint_output,
        debug=debug,
    )
