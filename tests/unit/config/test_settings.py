import pytest

from backend.app.config.settings import get_settings, reset_settings_cache
from backend.app.services.llm_client import MockLLMClient, OpenAILLMClient, create_llm_client


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_settings_cache()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)


def test_default_settings_use_mock() -> None:
    settings = get_settings()
    assert settings.llm_provider == "mock"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.database_url == "sqlite:///deliverylint.db"


def test_create_llm_client_defaults_to_mock() -> None:
    client = create_llm_client()
    assert isinstance(client, MockLLMClient)


def test_create_llm_client_with_fixtures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    reset_settings_cache()
    client = create_llm_client(use_fixtures=True)
    assert isinstance(client, MockLLMClient)
    assert client.fact_responses


def test_create_llm_client_openai_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    reset_settings_cache()
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        create_llm_client()


def test_create_llm_client_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    reset_settings_cache()
    client = create_llm_client()
    assert isinstance(client, OpenAILLMClient)
    assert client.model == "gpt-4o"


def test_invalid_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    reset_settings_cache()
    with pytest.raises(ValueError, match="Invalid LLM_PROVIDER"):
        get_settings()
