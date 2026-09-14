"""Provider abstraction for large-language-model calls.

Both OpenRouter and Ollama expose the same OpenAI-compatible
``POST /chat/completions`` API, so a single ``OpenAICompatibleProvider``
serves both — the only difference is the base URL and the API key.
``MockProvider`` returns a canned response with no network, which is what
the tests and the default ("mock") configuration use.
"""

import requests

from ai_agent import config


class ProviderError(RuntimeError):
    """A configured model provider could not produce a usable response."""


class LLMProvider:
    """Base contract every provider must implement."""

    def complete(self, system, user, **kwargs):
        """Return the model's text response for the given messages.

        Args:
            system: system prompt string.
            user: user message string.
            **kwargs: optional provider-specific options.

        Returns:
            str: the model's response content.
        """
        raise NotImplementedError

    @property
    def model_name(self):
        return getattr(self, "model", "unknown")


class OpenAICompatibleProvider(LLMProvider):
    """Calls any OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(self, base_url, api_key, model):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(self, system, user, temperature=0.2, timeout=120):
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Text model request failed: {exc}") from exc


class OpenRouterProvider(OpenAICompatibleProvider):
    """Cloud provider via OpenRouter."""

    def __init__(self, model=None, api_key=None):
        super().__init__(
            base_url=config.OPENROUTER_BASE_URL,
            api_key=(api_key if api_key is not None else config.OPENROUTER_API_KEY),
            model=model or config.OPENROUTER_MODEL,
        )


class OllamaProvider(OpenAICompatibleProvider):
    """Local provider via Ollama's OpenAI-compatible endpoint."""

    def __init__(self, model=None, base_url=None):
        super().__init__(
            base_url=base_url or config.OLLAMA_BASE_URL,
            # Ollama's /v1 endpoint accepts any key, including this placeholder.
            api_key="ollama",
            model=model or config.OLLAMA_MODEL,
        )


class MockProvider(LLMProvider):
    """Deterministic offline provider for tests and the default setup.

    Returns a canned structured JSON response that mirrors what a real
    model is asked to produce.
    """

    DEFAULT_OUTPUT = (
        '{"decision_type": "alert", '
        '"execution_type": "notification", '
        '"target_device": "none", '
        '"device_state": "none", '
        '"category": "alert", '
        '"recommendation": "Check tank level and sensor readings.", '
        '"explanation": "This is mock output generated offline for testing.", '
        '"confidence": 0.8}'
    )

    def __init__(self, output=None):
        self.output = output if output is not None else self.DEFAULT_OUTPUT
        self.model = "mock-llm"

    def complete(self, system, user, **kwargs):
        return self.output


def get_provider():
    """Return the provider instance selected by ``config.AI_PROVIDER``."""
    provider_name = config.AI_PROVIDER
    if provider_name == "openrouter":
        return OpenRouterProvider()
    if provider_name == "ollama":
        return OllamaProvider()
    if provider_name == "mock":
        return MockProvider()
    raise ValueError(f"Unknown AI_PROVIDER: {provider_name!r}")


class VLMProvider:
    model_name = "unknown"

    def complete(self, system, user, image_data_url, **kwargs):
        raise NotImplementedError


class OpenRouterVLMProvider(VLMProvider):
    def __init__(self, model=None, api_key=None, base_url=None):
        self.model_name = model or config.VLM_MODEL
        self.api_key = api_key if api_key is not None else config.OPENROUTER_API_KEY
        self.base_url = (base_url or config.OPENROUTER_BASE_URL).rstrip("/")

    def complete(
        self,
        system,
        user,
        image_data_url,
        temperature=0.2,
        timeout=None,
    ):
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_data_url},
                                },
                            ],
                        },
                    ],
                    "temperature": temperature,
                },
                timeout=timeout or config.VLM_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Vision model request failed: {exc}") from exc


class MockVLMProvider(VLMProvider):
    model_name = "mock-vlm"
    output = MockProvider.DEFAULT_OUTPUT

    def complete(self, system, user, image_data_url, **kwargs):
        return self.output


def get_vlm_provider():
    if config.VLM_PROVIDER == "openrouter":
        return OpenRouterVLMProvider()
    if config.VLM_PROVIDER == "mock":
        return MockVLMProvider()
    raise ValueError(f"Unknown VLM_PROVIDER: {config.VLM_PROVIDER!r}")
