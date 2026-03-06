"""Encryption helper — Fernet symmetric encryption with keychain-backed key."""

import logging
import os
import subprocess

from cryptography.fernet import Fernet

log = logging.getLogger("nanoclaw.crypto")

_KEYCHAIN_SERVICE = "NANOCLAW_DB_KEY"
_fernet: Fernet | None = None


def _keychain_get() -> str | None:
    """Read encryption key from macOS Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", _KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=5,
        )
        key = result.stdout.strip()
        return key if result.returncode == 0 and key else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _keychain_set(key: str):
    """Store encryption key in macOS Keychain."""
    subprocess.run(
        [
            "security", "add-generic-password",
            "-s", _KEYCHAIN_SERVICE,
            "-a", "nanoclaw",
            "-w", key,
            "-U",
        ],
        capture_output=True, text=True, timeout=5,
    )


def _env_key_path():
    """Fallback key file for Linux (no Keychain)."""
    from ..config import NANOCLAW_HOME
    return NANOCLAW_HOME / ".db_key"


def _get_fernet() -> Fernet:
    """Get or create the Fernet instance, generating a key if needed."""
    global _fernet
    if _fernet is not None:
        return _fernet

    key = None

    # Try macOS Keychain first
    if os.uname().sysname == "Darwin":
        key = _keychain_get()
        if not key:
            key = Fernet.generate_key().decode()
            _keychain_set(key)
            log.info("Generated new encryption key (stored in Keychain)")
    else:
        # Linux fallback: key file with restricted permissions
        key_path = _env_key_path()
        if key_path.exists():
            key = key_path.read_text().strip()
        else:
            key = Fernet.generate_key().decode()
            key_path.write_text(key)
            key_path.chmod(0o600)
            log.info("Generated new encryption key (stored in %s)", key_path)

    _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a string, return base64-encoded ciphertext."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt base64-encoded ciphertext back to string."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()
