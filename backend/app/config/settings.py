"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    openai_api_key: str | None
    openai_model: str
    database_url: str

    @property
    def use_openai(self) -> bool:
        return self.llm_provider == "openai"


@lru_cache
def get_settings() -> Settings:
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider not in {"mock", "openai"}:
        msg = f"Invalid LLM_PROVIDER={provider!r}; expected 'mock' or 'openai'"
        raise ValueError(msg)
    return Settings(
        llm_provider=provider,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///deliverylint.db"),
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()
