"""Configuration for the quality-gated vision-language recommendation agent.

Settings are read from the repository-root ``.env`` file without overriding
environment variables supplied by the process, matching ``ai_agent``.
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
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_env_file()

OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
VLM_PROVIDER = os.environ.get("VLM_PROVIDER", "openrouter").lower()
VLM_MODEL = os.environ.get("VLM_MODEL", "qwen/qwen3-vl-8b-instruct")

# The image is read from Django media and encoded locally before it is sent to
# OpenRouter, so private/local media does not need to be publicly reachable.
VLM_REQUEST_TIMEOUT_SECONDS = int(os.environ.get("VLM_REQUEST_TIMEOUT_SECONDS", "120"))
