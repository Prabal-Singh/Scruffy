from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    """Connection settings for the local Ollama inference server."""

    base_url: str = "http://192.168.0.7:11434"
    model: str = "qwen2.5:14b"
    timeout_seconds: float = 120.0

    @classmethod
    def from_env(cls) -> OllamaConfig:
        return cls(
            base_url=os.environ.get("SCRUFFY_OLLAMA_URL", cls.base_url),
            model=os.environ.get("SCRUFFY_OLLAMA_MODEL", cls.model),
            timeout_seconds=float(os.environ.get("SCRUFFY_OLLAMA_TIMEOUT", cls.timeout_seconds)),
        )
