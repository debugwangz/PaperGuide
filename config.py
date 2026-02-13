# PaperGuide configuration
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM Provider: "openai" or "claude"
    llm_provider: str = "openai"

    # OpenAI settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str | None = None

    # Claude settings
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    claude_base_url: str | None = None

    # Multimodal support (set to False if model doesn't support images)
    support_images: bool = True

    # Search provider: "brave" (more to come)
    search_provider: str = "brave"
    brave_api_key: str = ""

    # Output directory
    output_dir: str = "outputs"

    class Config:
        env_file = ".env"
        extra = "ignore"


# 单例模式，但支持重新加载
_settings: Settings | None = None


def get_settings(reload: bool = False) -> Settings:
    """获取配置，reload=True 时重新读取 .env 文件"""
    global _settings
    if _settings is None or reload:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置（修改 .env 后调用）"""
    return get_settings(reload=True)
