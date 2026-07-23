"""DeepSeek API client. Handles completion with JSON mode."""
import json
import os
from typing import Any

class DeepSeekClient:
    """OpenAI-compatible client for DeepSeek chat completion."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        from openai import OpenAI
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.last_content: str | None = None
        self.last_response_data: dict | None = None

    def complete_json(self, messages: list[dict[str, str]], temperature: float = 0.1, max_tokens: int = 1800) -> dict[str, Any]:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content
        self.last_content = content
        self.last_response_data = resp.model_dump() if hasattr(resp, "model_dump") else None
        return json.loads(content)

    @classmethod
    def from_env(cls) -> "DeepSeekClient":
        return cls()

