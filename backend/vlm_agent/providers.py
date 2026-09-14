"""OpenAI-compatible providers for text-only and image-plus-text VLM prompts."""

import requests

from vlm_agent import config


class VLMProvider:
    model_name = "unknown"

    def complete(self, system, user_text, image_data_url=None, **kwargs):
        raise NotImplementedError


class OpenRouterVLMProvider(VLMProvider):
    def __init__(self, model=None, api_key=None, base_url=None):
        self.model_name = model or config.VLM_MODEL
        self.api_key = api_key if api_key is not None else config.OPENROUTER_API_KEY
        self.base_url = (base_url or config.OPENROUTER_BASE_URL).rstrip("/")

    def complete(self, system, user_text, image_data_url=None, temperature=0.2, timeout=None):
        user_content = user_text
        if image_data_url:
            user_content = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]

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
                    {"role": "user", "content": user_content},
                ],
                "temperature": temperature,
            },
            timeout=timeout or config.VLM_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


class MockVLMProvider(VLMProvider):
    model_name = "mock-vlm"
    output = (
        '{"decision_type": "alert", "execution_type": "notification", '
        '"target_device": "none", "device_state": "none", "category": "alert", '
        '"recommendation": "Review the current farm conditions.", '
        '"explanation": "Mock VLM output for testing.", "confidence": 0.8}'
    )

    def complete(self, system, user_text, image_data_url=None, **kwargs):
        return self.output


def get_provider():
    if config.VLM_PROVIDER == "openrouter":
        return OpenRouterVLMProvider()
    if config.VLM_PROVIDER == "mock":
        return MockVLMProvider()
    raise ValueError(f"Unknown VLM_PROVIDER: {config.VLM_PROVIDER!r}")
