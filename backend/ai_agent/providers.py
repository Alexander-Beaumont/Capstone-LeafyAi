"""Provider abstraction for large-language-model calls.

Both OpenRouter and Ollama expose the same OpenAI-compatible
``POST /chat/completions`` API, so a single ``OpenAICompatibleProvider``
serves both — the only difference is the base URL and the API key.
``MockProvider`` returns a canned response with no network, which is what
the tests and the default ("mock") configuration use.
"""

import requests

from ai_agent import config


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


class OpenAICompatibleProvider(LLMProvider):
    """Calls any OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(self, base_url, api_key, model):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(self, system, user, temperature=0.2, timeout=120):
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
