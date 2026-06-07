"""
DeepSeek 客户端 - OpenAI 兼容 API。

读 .env:
  DEEPSEEK_API_KEY     (必填)
  DEEPSEEK_BASE_URL    默认 https://api.deepseek.com
  DEEPSEEK_MODEL       默认 deepseek-v4-pro

接口:
  llm.chat(messages, **kwargs) -> str
  llm.chat_json(messages) -> dict   (强制 JSON 输出)
"""
from __future__ import annotations
import os
import json
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
        self.timeout = timeout
        self._client: OpenAI | None = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _ensure(self):
        if not self.available:
            raise RuntimeError(
                "DEEPSEEK_API_KEY 未设置 - 请在 .env 文件中填入,或使用 --no-llm 模式"
            )
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        **kwargs,
    ) -> str:
        """普通对话,返回文本。"""
        self._ensure()
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error("DeepSeek chat failed: %s", e)
            raise

    def chat_json(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> dict:
        """要求 JSON 输出。解析失败时自动重试,并尝试一次修复。"""
        self._ensure()
        last_err: Exception | None = None

        for i in range(2):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature if i == 0 else min(temperature, 0.2),
                    max_tokens=max_tokens if i == 0 else int(max_tokens * 1.5),
                    response_format={"type": "json_object"},
                )
                content = resp.choices[0].message.content or "{}"
                return json.loads(content)
            except json.JSONDecodeError as e:
                last_err = e
                logger.warning("DeepSeek JSON 解析失败(第 %s 次): %s, content=%s", i + 1, e, content[:300])
                try:
                    repaired = self._repair_json(content)
                    return json.loads(repaired)
                except Exception as repair_err:
                    last_err = repair_err
            except Exception as e:
                last_err = e
                logger.warning("DeepSeek chat_json 调用失败(第 %s 次): %s", i + 1, e)

        logger.error("DeepSeek chat_json failed after retries: %s", last_err)
        raise last_err if last_err else RuntimeError("DeepSeek chat_json failed")

    def _repair_json(self, broken_content: str) -> str:
        """
        让模型将不合法 JSON 修复为合法 JSON 对象。
        """
        self._ensure()
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是 JSON 修复器。只输出一个合法 JSON 对象，不要任何解释。",
                },
                {
                    "role": "user",
                    "content": f"请修复以下 JSON 文本为合法 JSON 对象:\n{broken_content}",
                },
            ],
            temperature=0.0,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or "{}"


_default_client: LLMClient | None = None


def get_llm() -> LLMClient:
    """全局单例。"""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
