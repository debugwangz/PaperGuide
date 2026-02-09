from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM Provider
    llm_provider: str = "openai"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str | None = None
    
    # Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    anthropic_base_url: str | None = None
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/tinylearn.db"
    
    # Versions
    enrich_version: str = "v1"
    report_version: str = "v1"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
