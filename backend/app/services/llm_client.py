"""LLM client protocol, mock, and provider implementations."""

import json
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from backend.app.config.fact_extraction_config import FactExtractionConfig
from backend.app.config.settings import get_settings
from backend.app.config.target_document_config import TargetDocumentConfig
from backend.app.schemas.fact_parser import ExtractProjectFactsInput, ProjectFactLLMResponse
from backend.app.schemas.enums import DocType, FactCategory
from backend.app.schemas.source_profile import ProfileSourceArgs, SourceProfileInference
from backend.app.schemas.target_parser import ParseTargetDocumentInput, TargetDocumentLLMResponse
from backend.app.services.llm_sanitize import coerce_llm_payload

T = TypeVar("T", bound=BaseModel)


class LLMResponseError(Exception):
    """Raised when the LLM returns JSON that cannot be validated even after coercion."""


class LLMClient(Protocol):
    async def infer_source_profile(self, args: ProfileSourceArgs) -> SourceProfileInference: ...

    async def infer_project_facts(
        self,
        input: ExtractProjectFactsInput,
        config: FactExtractionConfig,
    ) -> ProjectFactLLMResponse: ...

    async def infer_target_parse(
        self,
        input: ParseTargetDocumentInput,
        config: TargetDocumentConfig,
    ) -> TargetDocumentLLMResponse: ...


_default_client: "LLMClient | None" = None


def get_default_llm_client() -> "LLMClient":
    global _default_client
    if _default_client is None:
        _default_client = create_llm_client()
    return _default_client


def set_default_llm_client(client: "LLMClient | None") -> None:
    global _default_client
    _default_client = client


def create_llm_client(*, use_fixtures: bool = False) -> "LLMClient":
    """Build an LLM client from environment settings."""
    settings = get_settings()
    if settings.use_openai:
        if not settings.openai_api_key:
            msg = "OPENAI_API_KEY is required when LLM_PROVIDER=openai"
            raise ValueError(msg)
        return OpenAILLMClient(api_key=settings.openai_api_key, model=settings.openai_model)

    if use_fixtures:
        from backend.app.fixtures.mock_pipeline_outputs import (
            MOCK_FACT_RESPONSES,
            MOCK_SOURCE_INFERENCES,
            MOCK_TARGET_RESPONSES,
        )

        return MockLLMClient(
            source_inferences=MOCK_SOURCE_INFERENCES,
            fact_responses=MOCK_FACT_RESPONSES,
            target_responses=MOCK_TARGET_RESPONSES,
        )
    return MockLLMClient()


def _schema_prompt(response_model: type[BaseModel]) -> str:
    return json.dumps(response_model.model_json_schema(), indent=2)


class MockLLMClient:
    """Returns fixture-backed responses; overridden by pipeline fixtures."""

    def __init__(
        self,
        source_inferences: dict[str, SourceProfileInference] | None = None,
        fact_responses: dict[str, ProjectFactLLMResponse] | None = None,
        target_responses: dict[str, TargetDocumentLLMResponse] | None = None,
    ) -> None:
        self.source_inferences = source_inferences or {}
        self.fact_responses = fact_responses or {}
        self.target_responses = target_responses or {}

    async def infer_source_profile(self, args: ProfileSourceArgs) -> SourceProfileInference:
        if args.document.id in self.source_inferences:
            return self.source_inferences[args.document.id]
        from backend.app.services.source_profiler import build_mock_inference

        return build_mock_inference(args)

    async def infer_project_facts(
        self,
        input: ExtractProjectFactsInput,
        config: FactExtractionConfig,
    ) -> ProjectFactLLMResponse:
        del config
        if input.document.id in self.fact_responses:
            return self.fact_responses[input.document.id]
        return ProjectFactLLMResponse(facts=[], warnings=[])

    async def infer_target_parse(
        self,
        input: ParseTargetDocumentInput,
        config: TargetDocumentConfig,
    ) -> TargetDocumentLLMResponse:
        del config
        if input.document.id in self.target_responses:
            return self.target_responses[input.document.id]
        return TargetDocumentLLMResponse(observed_content=[], sections=[], claims=[], warnings=[])


class OpenAILLMClient:
    """Structured OpenAI chat completions via JSON schema response format."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

    def _response_format(self, response_model: type[BaseModel]) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "schema": response_model.model_json_schema(),
                "strict": False,
            },
        }

    async def _complete_json(self, prompt: str, response_model: type[T]) -> T:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a structured document analysis assistant. "
                        "Return JSON that matches the provided schema exactly. "
                        "Use enum string values as defined in the schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": self._response_format(response_model),
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        coerced = coerce_llm_payload(parsed, response_model)
        try:
            return response_model.model_validate(coerced)
        except ValidationError as exc:
            msg = f"LLM response failed validation for {response_model.__name__}: {exc}"
            raise LLMResponseError(msg) from exc

    async def infer_source_profile(self, args: ProfileSourceArgs) -> SourceProfileInference:
        user_hints = ""
        if args.input is not None:
            user_hints = (
                f"\nUser hints: doc_type={args.input.user_provided_doc_type}, "
                f"origin={args.input.user_provided_origin}, "
                f"status={args.input.user_provided_status}, "
                f"recency_date={args.input.user_provided_recency_date}"
            )
        prompt = (
            "Classify this reference document. Infer doc type, origin, status, recency, "
            "observed content categories, reliability flags, and a short summary. "
            "Do not extract project facts.\n"
            "For observed_content, use only these exact category values: "
            f"{[category.value for category in FactCategory]}.\n"
            f"{user_hints}\n\n"
            f"JSON schema:\n{_schema_prompt(SourceProfileInference)}\n\n"
            f"Document text:\n{args.document.text[:12000]}"
        )
        return await self._complete_json(prompt, SourceProfileInference)

    async def infer_project_facts(
        self,
        input: ExtractProjectFactsInput,
        config: FactExtractionConfig,
    ) -> ProjectFactLLMResponse:
        prompt = (
            "Extract project facts from this reference document. "
            "Each fact must include evidence.quote from the source text.\n"
            f"Source profile doc_type: {input.source_profile.doc_type.value}\n"
            f"Allowed fact types: {[t.value for t in config.target_fact_types]}\n"
            f"Extraction guidance: {config.extraction_guidance}\n"
            f"Status guidance: {config.status_guidance}\n\n"
            f"JSON schema:\n{_schema_prompt(ProjectFactLLMResponse)}\n\n"
            f"Document text:\n{input.document.text[:12000]}"
        )
        return await self._complete_json(prompt, ProjectFactLLMResponse)

    async def infer_target_parse(
        self,
        input: ParseTargetDocumentInput,
        config: TargetDocumentConfig,
    ) -> TargetDocumentLLMResponse:
        prompt = (
            "Parse this target document into sections and checkable claims. "
            "Each claim must include location.quote from the target text.\n"
            f"Target doc type: {input.target_doc_type.value}\n"
            f"Expected content categories: {[c.value for c in config.expected_content]}\n"
            f"Allowed claim types: {[t.value for t in config.target_claim_types]}\n"
            f"Parsing guidance: {config.parsing_guidance}\n"
            f"Rubric guidance: {config.rubric_guidance}\n\n"
            f"JSON schema:\n{_schema_prompt(TargetDocumentLLMResponse)}\n\n"
            f"Document text:\n{input.document.text[:12000]}"
        )
        return await self._complete_json(prompt, TargetDocumentLLMResponse)
