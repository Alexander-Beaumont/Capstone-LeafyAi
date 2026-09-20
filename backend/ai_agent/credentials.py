import os

from django.core.exceptions import ImproperlyConfigured


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise ImproperlyConfigured("Install the cryptography package to use encrypted AI credentials.") from exc
    key = os.environ.get("AI_SETTINGS_ENCRYPTION_KEY", "").strip()
    if not key:
        raise ImproperlyConfigured(
            "AI_SETTINGS_ENCRYPTION_KEY is required to store or read AI API keys."
        )
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured("AI_SETTINGS_ENCRYPTION_KEY must be a valid Fernet key.") from exc


def encrypt_api_key(value):
    if not value:
        return ""
    return _fernet().encrypt(str(value).encode("utf-8")).decode("ascii")


def decrypt_api_key(value):
    if not value:
        return ""
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except Exception as exc:
        raise ImproperlyConfigured("Stored AI API key cannot be decrypted with the configured key.") from exc


def mask_api_key(encrypted_value):
    if not encrypted_value:
        return ""
    value = decrypt_api_key(encrypted_value)
    return f"••••{value[-4:]}" if value else ""
