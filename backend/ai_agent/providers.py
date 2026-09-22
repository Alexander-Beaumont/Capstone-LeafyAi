"""OpenAI-compatible text and multi-image provider adapters."""
import requests

from ai_agent import config
from ai_agent.credentials import decrypt_api_key


class ProviderError(RuntimeError):
    def __init__(self, message, *, retryable=True):
        super().__init__(message)
        self.retryable = retryable


def _response_error(payload, fallback):
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if isinstance(error, str) and error:
            return error
        if payload.get("message"):
            return str(payload["message"])
    return fallback


class OpenAICompatibleProvider:
    def __init__(self, base_url, api_key, model, provider_name):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model
        self.provider_name = provider_name

    def _post(self, messages, temperature=0.2, timeout=120):
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model_name, "messages": messages, "temperature": temperature},
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise ProviderError(
                f"{self.provider_name} model request failed: {exc}",
                retryable=True,
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            retryable = (
                200 <= response.status_code < 300
                or response.status_code in {408, 409, 425, 429}
                or response.status_code >= 500
            )
            raise ProviderError(
                f"{self.provider_name} model request failed: response was not valid JSON",
                retryable=retryable,
            ) from exc

        if not 200 <= response.status_code < 300:
            detail = _response_error(payload, f"HTTP {response.status_code}")
            retryable = response.status_code in {408, 409, 425, 429} or response.status_code >= 500
            raise ProviderError(
                f"{self.provider_name} model request failed: {detail}",
                retryable=retryable,
            )

        try:
            content = payload["choices"][0]["message"]["content"]
        except (IndexError, KeyError, TypeError) as exc:
            detail = _response_error(payload, "response did not contain choices")
            raise ProviderError(
                f"{self.provider_name} model request failed: {detail}",
                retryable=True,
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError(
                f"{self.provider_name} model request failed: response contained no message content",
                retryable=True,
            )
        return content

    def complete(self, system, user, **kwargs):
        return self._post([{"role": "system", "content": system}, {"role": "user", "content": user}], **kwargs)


class OpenAICompatibleVLMProvider(OpenAICompatibleProvider):
    def complete(self, system, user, images=None, temperature=0.2, timeout=None, **kwargs):
        content = [{"type": "text", "text": user}]
        for item in images or []:
            content.extend([
                {"type": "text", "text": str(item.get("label") or "Camera image")},
                {"type": "image_url", "image_url": {"url": item["data_url"]}},
            ])
        return self._post([{"role": "system", "content": system}, {"role": "user", "content": content}], temperature=temperature, timeout=timeout or config.VLM_REQUEST_TIMEOUT_SECONDS)


class MockProvider:
    provider_name = "mock"
    model_name = "mock-llm"
    DEFAULT_OUTPUT = '{"image_observations":[],"recommendations":[{"device_id":null,"decision_type":"alert","target_device":"none","device_state":"none","category":"alert","recommendation":"Inspect farm.","explanation":"Offline mock recommendation.","confidence":0.8}]}'

    def __init__(self, output=None, model_name=None):
        self.output = output or self.DEFAULT_OUTPUT
        if model_name:
            self.model_name = model_name

    def complete(self, system, user, **kwargs):
        return self.output


class MockVLMProvider(MockProvider):
    model_name = "mock-vlm"


def _connection(provider_name, api_key):
    if provider_name == "openrouter":
        return config.OPENROUTER_BASE_URL, api_key
    if provider_name == "ollama":
        return config.OLLAMA_BASE_URL, "ollama"
    raise ValueError(f"Unknown provider: {provider_name!r}")


def get_provider(configuration=None):
    if configuration is None:
        provider_name, model, api_key = config.AI_PROVIDER, config.OPENROUTER_MODEL, config.OPENROUTER_API_KEY
        if provider_name == "ollama":
            model = config.OLLAMA_MODEL
    else:
        provider_name, model = configuration.llm_provider, configuration.llm_model
        api_key = decrypt_api_key(configuration.llm_api_key_encrypted)
    if provider_name == "mock":
        return MockProvider(model_name=model)
    base_url, api_key = _connection(provider_name, api_key)
    return OpenAICompatibleProvider(base_url, api_key, model, provider_name)


def get_vlm_provider(configuration=None):
    if configuration is None:
        provider_name, model, api_key = config.VLM_PROVIDER, config.VLM_MODEL, config.OPENROUTER_API_KEY
    else:
        provider_name, model = configuration.vlm_provider, configuration.vlm_model
        api_key = decrypt_api_key(configuration.vlm_api_key_encrypted)
    if provider_name == "mock":
        return MockVLMProvider(model_name=model)
    base_url, api_key = _connection(provider_name, api_key)
    return OpenAICompatibleVLMProvider(base_url, api_key, model, provider_name)
