from backend.app.schemas.enums import FactCategory
from backend.app.schemas.source_profile import SourceProfileInference
from backend.app.services.llm_sanitize import coerce_llm_payload


def test_coerce_invalid_fact_category_alias() -> None:
    payload = {
        "inferred_doc_type": "CLIENT_EMAIL",
        "doc_type_confidence": 0.9,
        "inferred_origin": "client",
        "origin_confidence": 0.9,
        "inferred_status": "informal",
        "status_confidence": 0.9,
        "observed_content": ["scope", "clientRequests", "roles"],
        "reliability_flags": [],
        "summary": "test",
    }
    coerced = coerce_llm_payload(payload, SourceProfileInference)
    result = SourceProfileInference.model_validate(coerced)
    assert "responsibilities" in [item.value for item in result.observed_content]
    assert FactCategory.SCOPE in result.observed_content


def test_coerce_drops_unknown_fact_categories() -> None:
    payload = {
        "inferred_doc_type": "CLIENT_EMAIL",
        "doc_type_confidence": 0.9,
        "inferred_origin": "client",
        "origin_confidence": 0.9,
        "inferred_status": "informal",
        "status_confidence": 0.9,
        "observed_content": ["scope", "totally_invalid_category"],
        "reliability_flags": [],
        "summary": "test",
    }
    coerced = coerce_llm_payload(payload, SourceProfileInference)
    result = SourceProfileInference.model_validate(coerced)
    assert result.observed_content == [FactCategory.SCOPE]
