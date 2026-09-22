"""AI provider/model configuration.

Per-farm database settings are authoritative for normal recommendation runs.
Environment values remain deployment defaults for compatibility and direct
provider-factory callers. A repo-root .env is loaded without overriding the
process environment.

If neither the shell nor .env sets AI_PROVIDER, the default provider is
"mock", which requires no API key and no network.
"""

import os
from pathlib import Path


def _load_env_file(env_path=None):
    env_path = Path(env_path) if env_path else Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()

        key, separator, value = line.partition("=")
        if not separator:
            continue

        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ("'", '"')
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


_load_env_file()

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

# Vision-language model. It deliberately shares the OpenRouter connection
# settings with the text model while allowing an independently selected model.
VLM_PROVIDER = os.environ.get("VLM_PROVIDER", "openrouter").lower()
VLM_MODEL = os.environ.get("VLM_MODEL", "qwen/qwen3-vl-8b-instruct")
VLM_REQUEST_TIMEOUT_SECONDS = int(
    os.environ.get("VLM_REQUEST_TIMEOUT_SECONDS", "120")
)
