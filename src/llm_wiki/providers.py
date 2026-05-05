from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
import subprocess
from urllib import request, error

from .config import ProviderConfig
from .models import CompletionResult


class ProviderError(RuntimeError):
    pass


class BaseProvider(ABC):
    @abstractmethod
    def complete(self, system: str, prompt: str) -> CompletionResult:
        raise NotImplementedError


class OpenAIStyleProvider(BaseProvider):
    def __init__(self, config: ProviderConfig, require_api_key: bool = True):
        self.model = config.model
        self.base_url = (config.base_url or "").rstrip("/")
        if not self.base_url:
            raise ProviderError("Missing base_url for OpenAI-style provider.")
        self.api_key: str | None = None
        if not require_api_key:
            if config.api_key_env:
                self.api_key = os.environ.get(config.api_key_env)
            return
        if not config.api_key_env:
            raise ProviderError("Missing api_key_env for openai_compatible provider.")
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            raise ProviderError(f"Environment variable {config.api_key_env} is not set.")
        self.api_key = api_key

    def complete(self, system: str, prompt: str) -> CompletionResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with request.urlopen(req) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Provider request failed: {details}") from exc
        except error.URLError as exc:
            raise ProviderError(f"Provider request failed: {exc.reason}") from exc
        return CompletionResult(text=parse_openai_style_response(body))

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


class OpenAICompatibleProvider(OpenAIStyleProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config, require_api_key=True)


class LMStudioProvider(OpenAIStyleProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config, require_api_key=False)


class AnthropicProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        self.model = config.model
        if not config.api_key_env:
            raise ProviderError("Missing api_key_env for anthropic provider.")
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            raise ProviderError(f"Environment variable {config.api_key_env} is not set.")
        self.api_key = api_key

    def complete(self, system: str, prompt: str) -> CompletionResult:
        payload = {
            "model": self.model,
            "system": system,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
        }
        req = request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Provider request failed: {details}") from exc
        parts = [part["text"] for part in body["content"] if part["type"] == "text"]
        return CompletionResult(text="\n".join(parts))


class CommandProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        if not config.command:
            raise ProviderError("Missing command for command provider.")
        self.command = config.command
        self.model = config.model

    def complete(self, system: str, prompt: str) -> CompletionResult:
        payload = json.dumps(
            {
                "model": self.model,
                "system": system,
                "prompt": prompt,
            }
        )
        result = subprocess.run(
            self.command,
            input=payload,
            text=True,
            capture_output=True,
            shell=True,
            check=False,
        )
        if result.returncode != 0:
            raise ProviderError(result.stderr.strip() or "Command provider failed.")
        body = json.loads(result.stdout)
        return CompletionResult(text=body["text"])


def build_provider(config: ProviderConfig) -> BaseProvider:
    if config.kind == "openai_compatible":
        return OpenAICompatibleProvider(config)
    if config.kind == "lm_studio":
        return LMStudioProvider(config)
    if config.kind == "anthropic":
        return AnthropicProvider(config)
    if config.kind == "command":
        return CommandProvider(config)
    raise ProviderError(f"Unsupported provider kind: {config.kind}")


def parse_openai_style_response(body: dict) -> str:
    if "error" in body:
        raise ProviderError(f"Provider returned an error: {stringify_provider_error(body['error'])}")
    if "choices" in body and body["choices"]:
        message = body["choices"][0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            if text_parts:
                return "\n".join(part for part in text_parts if part)
        text = body["choices"][0].get("text")
        if isinstance(text, str):
            return text
    if isinstance(body.get("message"), str):
        raise ProviderError(f"Provider returned a non-completion response: {body['message']}")
    raise ProviderError(
        "Provider response did not include completion text. "
        f"Top-level keys: {', '.join(sorted(body.keys())) or '(none)'}"
    )


def stringify_provider_error(error_value: object) -> str:
    if isinstance(error_value, dict):
        if isinstance(error_value.get("message"), str) and error_value["message"].strip():
            return error_value["message"]
        if isinstance(error_value.get("error"), str) and error_value["error"].strip():
            return error_value["error"]
        if isinstance(error_value.get("code"), str):
            return json.dumps(error_value)
        return json.dumps(error_value)
    if isinstance(error_value, list):
        return ", ".join(str(item) for item in error_value)
    if isinstance(error_value, str):
        return error_value
    return repr(error_value)
