"""LLM client for PaperGuide.

Supports OpenAI and Claude APIs with optional multimodal (image) input.
"""
import json
import base64
import logging
import httpx
from pathlib import Path
from abc import ABC, abstractmethod

# 配置日志 - 同时输出到控制台和按日期分割的文件
import datetime

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_date = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = log_dir / f"paperguide_{log_date}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # 控制台
        logging.FileHandler(log_file, encoding="utf-8"),  # 文件
    ]
)
logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Type, TypeVar
from pydantic import BaseModel
from openai import OpenAI
from anthropic import Anthropic
from config import get_settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract LLM provider."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str,
                 images: list[Path] | None = None) -> str:
        """Generate text response."""
        pass

    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str,
                      schema: Type[T]) -> T:
        """Generate structured JSON response."""
        pass

    @property
    @abstractmethod
    def supports_images(self) -> bool:
        """Whether this provider supports image input."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=httpx.Timeout(600.0, connect=30.0),  # 10 分钟读取超时
            max_retries=3,
        )
        self.model = settings.openai_model
        self._supports_images = settings.support_images

    @property
    def supports_images(self) -> bool:
        return self._supports_images

    def _encode_image(self, image_path: Path) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _build_content(self, text: str, images: list[Path] | None) -> list[dict]:
        content = [{"type": "text", "text": text}]
        if images and self.supports_images:
            for img in images:
                b64 = self._encode_image(img)
                suffix = img.suffix.lower().lstrip(".")
                mime = f"image/{suffix}" if suffix in ["png", "jpg", "jpeg", "gif", "webp"] else "image/png"
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"}
                })
        return content

    def generate(self, system_prompt: str, user_prompt: str,
                 images: list[Path] | None = None) -> str:
        content = self._build_content(user_prompt, images)
        logger.info(f"[OpenAI] 调用模型: {self.model}")
        logger.info(f"[OpenAI] Prompt 长度: {len(user_prompt)} 字符")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content if images else user_prompt}
            ],
            max_tokens=8192,  # 与 OpenClaw 一致
            temperature=0.3,
        )
        result = response.choices[0].message.content or ""
        logger.info(f"[OpenAI] 响应长度: {len(result)} 字符")
        return result

    def generate_json(self, system_prompt: str, user_prompt: str,
                      schema: Type[T]) -> T:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = response.choices[0].message.content or "{}"
        return schema.model_validate(json.loads(content))


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self):
        settings = get_settings()
        kwargs = {
            "api_key": settings.anthropic_api_key,
            "timeout": httpx.Timeout(600.0, connect=30.0),  # 10 分钟读取超时
            "max_retries": 3,
        }
        if settings.claude_base_url:
            kwargs["base_url"] = settings.claude_base_url
        self.client = Anthropic(**kwargs)
        self.model = settings.claude_model
        self._supports_images = settings.support_images

    @property
    def supports_images(self) -> bool:
        return self._supports_images

    def _encode_image(self, image_path: Path) -> tuple[str, str]:
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        suffix = image_path.suffix.lower().lstrip(".")
        mime = f"image/{suffix}" if suffix in ["png", "jpg", "jpeg", "gif", "webp"] else "image/png"
        return data, mime

    def _build_content(self, text: str, images: list[Path] | None) -> list[dict]:
        content = []
        if images and self.supports_images:
            for img in images:
                data, mime = self._encode_image(img)
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": mime, "data": data}
                })
        content.append({"type": "text", "text": text})
        return content

    def generate(self, system_prompt: str, user_prompt: str,
                 images: list[Path] | None = None) -> str:
        content = self._build_content(user_prompt, images)
        logger.info(f"[Claude] 调用模型: {self.model}")
        logger.info(f"[Claude] Prompt 长度: {len(user_prompt)} 字符")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,  # 与 OpenClaw 一致
            system=system_prompt,
            messages=[{"role": "user", "content": content}]
        )
        result = response.content[0].text
        logger.info(f"[Claude] 响应长度: {len(result)} 字符")
        return result

    def generate_json(self, system_prompt: str, user_prompt: str,
                      schema: Type[T]) -> T:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        content = response.content[0].text.strip()
        # Extract JSON from markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1] == "```" else content
        return schema.model_validate(json.loads(content))


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    logger.info(f"初始化 LLM Provider: {provider}")
    if provider == "openai":
        logger.info(f"使用 OpenAI 模型: {settings.openai_model}")
        return OpenAIProvider()
    elif provider == "claude":
        logger.info(f"使用 Claude 模型: {settings.claude_model}")
        return ClaudeProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
