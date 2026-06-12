from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services.llm_client import OpenAILLMClient
from backend.app.schemas.source_profile import ProfileSourceArgs, ProfileSourceDocument


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
