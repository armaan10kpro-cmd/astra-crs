"""Model abstraction for local, API, and deterministic mock providers."""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, prompt: str, *, system: str = "") -> str:
        ...


class MockProvider(ModelProvider):
    """Deterministic offline provider for competition demos."""

    name = "mock"

    def complete(self, prompt: str, *, system: str = "") -> str:
        return json.dumps(
            {
                "root_cause": "Destination buffer is 32 bytes but memcpy copies strlen(msg)+1 bytes without bound check.",
                "proposed_change": "Reject inputs where n >= sizeof(buf) before memcpy; preserve normal behaviour for valid inputs.",
                "unified_diff": (
                    "--- a/demo_vuln.c\n"
                    "+++ b/demo_vuln.c\n"
                    "@@ -11,6 +11,9 @@ int parse_message(const char *msg) {\n"
                    "     char buf[32];\n"
                    "     size_t n = strlen(msg);\n"
                    "+    if (n >= sizeof(buf)) {\n"
                    "+        return -1;\n"
                    "+    }\n"
                    "     memcpy(buf, msg, n + 1);\n"
                ),
                "expected_security_property": "copy_length <= sizeof(buf) for all accepted inputs",
                "expected_behavioural_preservation": "valid inputs <=31 chars return first byte unchanged",
            }
        )


class LocalProvider(ModelProvider):
    """Placeholder for local model (llama.cpp, ollama, etc.)."""

    name = "local"

    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint or os.environ.get("ASTRA_LOCAL_MODEL_URL", "http://127.0.0.1:11434")

    def complete(self, prompt: str, *, system: str = "") -> str:
        try:
            import urllib.request

            body = json.dumps(
                {
                    "model": os.environ.get("ASTRA_LOCAL_MODEL", "codellama"),
                    "prompt": f"{system}\n\n{prompt}",
                    "stream": False,
                }
            ).encode()
            req = urllib.request.Request(
                f"{self.endpoint.rstrip('/')}/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            return data.get("response", "")
        except Exception as exc:
            raise RuntimeError(f"LocalProvider unavailable: {exc}") from exc


class OpenAICompatibleProvider(ModelProvider):
    """OpenAI-compatible chat completions API."""

    name = "openai-compatible"

    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or os.environ.get("ASTRA_API_MODEL", "gpt-4o-mini")

    def complete(self, prompt: str, *, system: str = "") -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        import urllib.request

        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system or "You are a security patch assistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]


def get_provider(name: str | None = None) -> ModelProvider:
    chosen = (name or os.environ.get("ASTRA_MODEL_PROVIDER", "mock")).lower()
    if chosen in ("mock", "deterministic"):
        return MockProvider()
    if chosen in ("local", "ollama"):
        return LocalProvider()
    if chosen in ("openai", "api", "openai-compatible"):
        return OpenAICompatibleProvider()
    return MockProvider()


def extract_json(text: str) -> dict[str, Any]:
    """Parse structured JSON from model output; reject malformed."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise ValueError("Model output is not valid JSON")
        obj = json.loads(m.group())
    required = {
        "root_cause",
        "proposed_change",
        "unified_diff",
        "expected_security_property",
        "expected_behavioural_preservation",
    }
    missing = required - set(obj.keys())
    if missing:
        raise ValueError(f"Malformed model output; missing keys: {sorted(missing)}")
    return obj
