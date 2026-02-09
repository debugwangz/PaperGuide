import json
from abc import ABC, abstractmethod
from typing import Type, TypeVar

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        """生成结构化 JSON 输出并解析为 Pydantic 模型"""
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model

    async def generate_json(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return schema.model_validate(data)


class ClaudeProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        kwargs = {"api_key": settings.anthropic_api_key}
        if settings.anthropic_base_url:
            kwargs["base_url"] = settings.anthropic_base_url
        self.client = AsyncAnthropic(**kwargs)
        self.model = settings.claude_model

    async def generate_json(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content[0].text
        # 提取 JSON（Claude 可能会包含额外文字）
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        data = json.loads(content)
        return schema.model_validate(data)


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "claude":
        return ClaudeProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
