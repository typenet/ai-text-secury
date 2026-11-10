"""API keys: só o hash SHA-256 é persistido; o valor aparece uma única vez na criação."""

import hashlib
import secrets

KEY_PREFIX = "ats_"


def generate_api_key() -> tuple[str, str, str]:
    """Retorna (chave, prefixo visível, hash)."""
    key = KEY_PREFIX + secrets.token_urlsafe(32)
    return key, key[:12], hash_api_key(key)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
