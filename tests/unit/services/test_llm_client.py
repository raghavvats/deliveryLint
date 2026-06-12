from unittest.mock import AsyncMock, patch

import pytest

from backend.app.schemas.source_profile import ProfileSourceArgs, ProfileSourceDocument
from backend.app.services.llm_client import OpenAILLMClient


@pytest.mark.asyncio
async def test_openai_client_coerces_invalid_observed_content() -> None:
    client = OpenAILLMClient(api_key="test-key")
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"inferred_doc_type":"CLIENT_EMAIL","doc_type_confidence":0.9,'
                        '"inferred_origin":"client","origin_confidence":0.9,'
                        '"inferred_status":"informal","status_confidence":0.9,'
                        '"observed_content":["scope","roles"],'
                        '"reliability_flags":[],"summary":"test"}'
                    )
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.raise_for_status = lambda: None
        mock_post.return_value.json = lambda: mock_response
        result = await client.infer_source_profile(
            ProfileSourceArgs(document=ProfileSourceDocument(id="d1", text="hello"))
        )

    assert result.inferred_doc_type.value == "CLIENT_EMAIL"
    assert "responsibilities" in [item.value for item in result.observed_content]


@pytest.mark.asyncio
async def test_openai_client_parses_response() -> None:
    client = OpenAILLMClient(api_key="test-key")
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"inferred_doc_type":"CLIENT_EMAIL","doc_type_confidence":0.9,'
                        '"inferred_origin":"client","origin_confidence":0.9,'
                        '"inferred_status":"informal","status_confidence":0.9,'
                        '"observed_content":["clientRequests"],'
                        '"reliability_flags":[],"summary":"test"}'
                    )
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.raise_for_status = lambda: None
        mock_post.return_value.json = lambda: mock_response
        result = await client.infer_source_profile(
            ProfileSourceArgs(document=ProfileSourceDocument(id="d1", text="hello"))
        )

    assert result.inferred_doc_type.value == "CLIENT_EMAIL"
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["response_format"]["type"] == "json_schema"


@pytest.mark.asyncio
async def test_openai_client_includes_schema_in_prompt() -> None:
    client = OpenAILLMClient(api_key="test-key")
    mock_response = {
        "choices": [{"message": {"content": '{"facts":[],"warnings":[]}'}}]
    }

    from backend.app.config.fact_extraction_config import FACT_EXTRACTION_CONFIG_BY_DOC_TYPE
    from backend.app.schemas.enums import DocType, InferenceSource, SourceOrigin, SourceStatus
    from backend.app.schemas.fact_parser import ExtractProjectFactsInput, FactParserDocument
    from backend.app.schemas.source_profile import SourceProfile

    profile = SourceProfile(
        id="sp1",
        document_id="d1",
        doc_type=DocType.SIGNED_SOW,
        doc_type_confidence=1.0,
        doc_type_source=InferenceSource.USER,
        origin=SourceOrigin.CLIENT,
        origin_confidence=1.0,
        origin_source=InferenceSource.USER,
        status=SourceStatus.SIGNED,
        status_confidence=1.0,
        status_source=InferenceSource.USER,
        authority_level=5,
        authority_rationale="signed",
        expected_content=[],
        observed_content=[],
        missing_expected_content=[],
        reliability_flags=[],
        summary="signed sow",
    )
    fact_input = ExtractProjectFactsInput(
        project_id="p1",
        document=FactParserDocument(id="d1", text="scope text"),
        source_profile=profile,
    )
    config = FACT_EXTRACTION_CONFIG_BY_DOC_TYPE[DocType.SIGNED_SOW]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.raise_for_status = lambda: None
        mock_post.return_value.json = lambda: mock_response
        await client.infer_project_facts(fact_input, config)

    prompt = mock_post.call_args.kwargs["json"]["messages"][1]["content"]
    assert "ProjectFactLLMResponse" in prompt
    assert "Allowed fact types" in prompt
