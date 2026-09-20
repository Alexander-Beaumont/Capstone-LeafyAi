"""Shared loading for the farm safety configuration."""

from pathlib import Path
import yaml
from django.conf import settings


def default_farm_config_path():
    """Return the project-level farm_config.yaml path."""
    return settings.BASE_DIR / "farm_config.yaml"


def load_farm_config(config_path=None):
    """Load the farm safety configuration from YAML."""
    path = Path(config_path) if config_path is not None else default_farm_config_path()
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
