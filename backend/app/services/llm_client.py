"""LLM client protocol, mock, and provider implementations."""

from typing import Protocol, TypeVar

from backend.app.config.fact_extraction_config import FactExtractionConfig
from backend.app.config.target_document_config import TargetDocumentConfig
from backend.app.schemas.fact_parser import ExtractProjectFactsInput, ProjectFactLLMResponse
from backend.app.schemas.source_profile import ProfileSourceArgs, SourceProfileInference
from backend.app.schemas.target_parser import ParseTargetDocumentInput, TargetDocumentLLMResponse

T = TypeVar("T")


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
        _default_client = MockLLMClient()
    return _default_client


def set_default_llm_client(client: "LLMClient") -> None:
    global _default_client
    _default_client = client


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
    """Structured OpenAI chat completions (Phase 5)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

    async def _complete_json(self, prompt: str, response_model: type[T]) -> T:
        import httpx

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return valid JSON matching the requested schema only.",
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        return response_model.model_validate_json(content)

    async def infer_source_profile(self, args: ProfileSourceArgs) -> SourceProfileInference:
        prompt = (
            "Classify this reference document. Return JSON for SourceProfileInference.\n\n"
            f"Document text:\n{args.document.text[:8000]}"
        )
        return await self._complete_json(prompt, SourceProfileInference)

    async def infer_project_facts(
        self,
        input: ExtractProjectFactsInput,
        config: FactExtractionConfig,
    ) -> ProjectFactLLMResponse:
        prompt = (
            "Extract project facts from this document. Return JSON for ProjectFactLLMResponse.\n"
            f"Allowed fact types: {[t.value for t in config.target_fact_types]}\n"
            f"Guidance: {config.extraction_guidance}\n\n"
            f"Document text:\n{input.document.text[:8000]}"
        )
        return await self._complete_json(prompt, ProjectFactLLMResponse)

    async def infer_target_parse(
        self,
        input: ParseTargetDocumentInput,
        config: TargetDocumentConfig,
    ) -> TargetDocumentLLMResponse:
        prompt = (
            "Parse this target document into sections and claims. "
            "Return JSON for TargetDocumentLLMResponse.\n"
            f"Allowed claim types: {[t.value for t in config.target_claim_types]}\n"
            f"Guidance: {config.parsing_guidance}\n\n"
            f"Document text:\n{input.document.text[:8000]}"
        )
        return await self._complete_json(prompt, TargetDocumentLLMResponse)
