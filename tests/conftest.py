"""Shared pytest fixtures."""

import pytest

from backend.app.config.settings import reset_settings_cache
from backend.app.services.llm_client import set_default_llm_client


@pytest.fixture(autouse=True)
def use_mock_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    reset_settings_cache()
    set_default_llm_client(None)
