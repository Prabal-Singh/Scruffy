from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from scruffy.llm.config import OllamaConfig

T = TypeVar("T", bound=BaseModel)


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    """Minimal HTTP client for Ollama on the Linux inference box."""

    def __init__(self, config: Optional[OllamaConfig] = None) -> None:
        self.config = config or OllamaConfig.from_env()

    @property
    def base_url(self) -> str:
        return self.config.base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OllamaError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise OllamaError(f"Cannot reach Ollama at {self.base_url}: {exc.reason}") from exc

    def list_models(self) -> list[dict[str, Any]]:
        request = urllib.request.Request(f"{self.base_url}/api/tags")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise OllamaError(f"Cannot reach Ollama at {self.base_url}: {exc.reason}") from exc
        return payload.get("models", [])

    def generate(self, prompt: str, *, json_mode: bool = False) -> str:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }
        if json_mode:
            payload["format"] = "json"
        result = self._post("/api/generate", payload)
        return str(result.get("response", "")).strip()

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0},
        }
        if json_mode:
            payload["format"] = "json"
        result = self._post("/api/chat", payload)
        message = result.get("message", {})
        return str(message.get("content", "")).strip()

    def parse_json(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return json.loads(cleaned)

    def chat_structured(
        self,
        messages: list[dict[str, str]],
        schema: Type[T],
    ) -> T:
        raw = self.chat(messages, json_mode=True)
        try:
            data = self.parse_json(raw)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise OllamaError(f"Invalid structured response: {raw!r}") from exc
