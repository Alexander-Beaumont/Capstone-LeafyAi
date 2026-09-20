"""
Django settings for the Leafy AI backend.
"""

import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent


def _load_repo_env(path=None):
    """Load the repository-root .env without overriding process variables.

    This keeps local development consistent with the existing AI/VLM config
    while allowing systemd/Docker/production to inject real environment values.
    """

    env_path = Path(path) if path else REPO_ROOT / ".env"
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


_load_repo_env()

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Development defaults.  Production deployment should override these.
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-op-bnk!dv73#$@@22z2qu9o(1#mr0a=v9t@$b_7b!wwf=erxc5",
)
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() in ("1", "true", "yes", "on")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "corsheaders",
    "rest_framework",
    # Leafy AI apps
    "cv",
    "telemetry",
    "sensor_ingest",
    "ai_agent.apps.AiAgentConfig",
    "farm_state",
    "growth",
    "accounts",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]
CORS_URLS_REGEX = r"^/api/.*$"
CORS_PREFLIGHT_MAX_AGE = 86400

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Sensor ingestion / ThingSpeak
# ---------------------------------------------------------------------------
# Secrets intentionally default to empty so the web backend can still start
# when external telemetry is not configured.  The collector validates them
# before it runs.
THINGSPEAK_CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID", "")
THINGSPEAK_READ_API_KEY = os.getenv("THINGSPEAK_READ_API_KEY", "")
SENSOR_INGEST_DEVICE_SLUG = os.getenv("SENSOR_INGEST_DEVICE_SLUG", "")
SENSOR_INGEST_SOURCE_KEY = os.getenv(
    "SENSOR_INGEST_SOURCE_KEY", "thingspeak-primary"
)

SENSOR_INGEST_POLL_SECONDS = int(os.getenv("SENSOR_INGEST_POLL_SECONDS", "30"))
SENSOR_INGEST_RECONCILE_SECONDS = int(
    os.getenv("SENSOR_INGEST_RECONCILE_SECONDS", "300")
)
SENSOR_INGEST_BACKFILL_RESULTS = int(
    os.getenv("SENSOR_INGEST_BACKFILL_RESULTS", "100")
)
SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS = int(
    os.getenv("SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS", "30")
)
SENSOR_INGEST_SENSOR_STALE_SECONDS = int(
    os.getenv("SENSOR_INGEST_SENSOR_STALE_SECONDS", "120")
)
SENSOR_INGEST_FEED_STALE_SECONDS = int(
    os.getenv("SENSOR_INGEST_FEED_STALE_SECONDS", "120")
)

SENSOR_INGEST_CONNECT_TIMEOUT_SECONDS = float(
    os.getenv("SENSOR_INGEST_CONNECT_TIMEOUT_SECONDS", "3.05")
)
SENSOR_INGEST_READ_TIMEOUT_SECONDS = float(
    os.getenv("SENSOR_INGEST_READ_TIMEOUT_SECONDS", "10")
)
SENSOR_INGEST_HTTP_RETRY_TOTAL = int(
    os.getenv("SENSOR_INGEST_HTTP_RETRY_TOTAL", "4")
)
SENSOR_INGEST_HTTP_RETRY_BACKOFF = float(
    os.getenv("SENSOR_INGEST_HTTP_RETRY_BACKOFF", "0.5")
)
SENSOR_INGEST_FAILURE_BACKOFF_BASE_SECONDS = int(
    os.getenv("SENSOR_INGEST_FAILURE_BACKOFF_BASE_SECONDS", "5")
)
SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS = int(
    os.getenv("SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS", "300")
)

# Farm-state trend summarisation.  Raw history stays in telemetry; only compact
# deterministic statistics are exposed to AI/farm-state consumers.
FARM_STATE_SENSOR_TREND_WINDOW_MINUTES = int(
    os.getenv("FARM_STATE_SENSOR_TREND_WINDOW_MINUTES", "30")
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        }
    },
    "loggers": {
        "sensor_ingest": {
            "handlers": ["console"],
            "level": os.getenv("SENSOR_INGEST_LOG_LEVEL", "INFO"),
            "propagate": False,
        }
    },
}
