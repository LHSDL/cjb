"""百炼 OpenAI 兼容客户端与安全错误映射。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from meeting_assistant.ai.prompts import PromptRequest


class AIAnalysisError(RuntimeError):
    """可安全展示且不包含敏感配置的 AI 错误。"""


class AIConfigurationError(AIAnalysisError):
    """AI 环境配置缺失或无效。"""


@dataclass(frozen=True, slots=True)
class DashScopeSettings:
    api_key: str = field(repr=False)
    base_url: str
    model: str
    timeout_seconds: float = 30

    @classmethod
    def from_env(cls, env_path: Path | str | None = None) -> "DashScopeSettings":
        path = Path(env_path) if env_path is not None else Path.cwd() / ".env"
        if path.exists():
            load_dotenv(path, override=False, encoding="utf-8-sig")

        names = ("DASHSCOPE_API_KEY", "DASHSCOPE_BASE_URL", "DASHSCOPE_MODEL")
        values = {name: os.getenv(name, "").strip() for name in names}
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise AIConfigurationError(
                "缺少AI配置：" + "、".join(missing) + "。会议与手工行动项功能仍可使用"
            )
        if not values["DASHSCOPE_BASE_URL"].startswith(("https://", "http://")):
            raise AIConfigurationError("DASHSCOPE_BASE_URL 必须是 HTTP(S) 地址")
        try:
            timeout = float(os.getenv("DASHSCOPE_TIMEOUT_SECONDS", "30"))
        except ValueError as error:
            raise AIConfigurationError("DASHSCOPE_TIMEOUT_SECONDS 必须是数字") from error
        if timeout <= 0:
            raise AIConfigurationError("DASHSCOPE_TIMEOUT_SECONDS 必须大于 0")
        return cls(
            api_key=values["DASHSCOPE_API_KEY"],
            base_url=values["DASHSCOPE_BASE_URL"].rstrip("/"),
            model=values["DASHSCOPE_MODEL"],
            timeout_seconds=timeout,
        )


class LLMClient(Protocol):
    def complete(self, prompt: PromptRequest) -> str: ...


class DashScopeClient:
    def __init__(self, settings: DashScopeSettings, *, sdk_client=None):
        self.settings = settings
        self.model_name = settings.model
        self._client = sdk_client or OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            max_retries=0,
        )

    def _request(self, prompt: PromptRequest):
        return self._client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False},
            temperature=0.1,
        )

    def complete(self, prompt: PromptRequest) -> str:
        for attempt in range(2):
            try:
                response = self._request(prompt)
                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise AIAnalysisError(
                        "模型返回了空内容，会议与手工行动项功能仍可使用"
                    )
                return content
            except AuthenticationError as error:
                raise AIAnalysisError(
                    "模型鉴权失败，请检查本地 DASHSCOPE_API_KEY；"
                    "会议与手工行动项功能仍可使用"
                ) from error
            except RateLimitError as error:
                raise AIAnalysisError(
                    "模型调用受限或免费额度已耗尽；会议与手工行动项功能仍可使用"
                ) from error
            except APITimeoutError as error:
                if attempt == 0:
                    continue
                raise AIAnalysisError(
                    "模型调用超时，会议与手工行动项功能仍可使用"
                ) from error
            except APIConnectionError as error:
                if attempt == 0:
                    continue
                raise AIAnalysisError(
                    "无法连接模型服务，会议与手工行动项功能仍可使用"
                ) from error
            except APIStatusError as error:
                raise AIAnalysisError(
                    f"模型服务返回 HTTP {error.status_code}；"
                    "会议与手工行动项功能仍可使用"
                ) from error
            except AIAnalysisError:
                raise
            except OpenAIError as error:
                raise AIAnalysisError(
                    "模型调用失败，会议与手工行动项功能仍可使用"
                ) from error
        raise AssertionError("unreachable")

