"""AI provider/model configuration.

Provider and model selection is driven by environment variables so the
application can switch between cloud (OpenRouter) and local (Ollama) models
without changing code.

The default provider is "mock", which requires no API key and no network —
so the agent runs out of the box. Set AI_PROVIDER=openrouter (plus
OPENROUTER_API_KEY) or AI_PROVIDER=ollama to go live.
"""

import os

# Which provider to use: "openrouter" | "ollama" | "mock"
AI_PROVIDER = os.environ.get("AI_PROVIDER", "mock")

# ------------------------------------------------------------------
# OpenRouter (cloud)
# ------------------------------------------------------------------
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
)

# ------------------------------------------------------------------
# Ollama (local)
# ------------------------------------------------------------------
# The :v1 path is Ollama's OpenAI-compatible endpoint.
OLLAMA_BASE_URL = os.environ.get(
    "OLLAMA_BASE_URL",
    "http://localhost:11434/v1",
)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
