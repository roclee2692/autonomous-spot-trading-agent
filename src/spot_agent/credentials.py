from __future__ import annotations

import getpass
import os
from dataclasses import dataclass

SERVICE_PREFIX = "autonomous-spot-trading-agent"


@dataclass(frozen=True)
class APICredentials:
    api_key: str
    api_secret: str
    source: str


def _service(environment: str) -> str:
    if environment not in {"testnet", "live"}:
        raise ValueError("credentials exist only for testnet or live")
    return f"{SERVICE_PREFIX}/{environment}"


def _env_names(environment: str) -> tuple[str, str]:
    prefix = f"BINANCE_{environment.upper()}"
    return f"{prefix}_API_KEY", f"{prefix}_API_SECRET"


def load_credentials(environment: str) -> APICredentials:
    key_name, secret_name = _env_names(environment)
    env_key, env_secret = os.getenv(key_name), os.getenv(secret_name)
    if env_key or env_secret:
        if not env_key or not env_secret:
            raise ValueError(f"both {key_name} and {secret_name} are required")
        return APICredentials(env_key.strip(), env_secret.strip(), "environment")
    try:
        import keyring
    except ImportError as exc:
        raise RuntimeError("keyring is required for local credential storage") from exc
    service = _service(environment)
    api_key = keyring.get_password(service, "api_key")
    api_secret = keyring.get_password(service, "api_secret")
    if not api_key or not api_secret:
        raise RuntimeError(
            f"no {environment} credentials found; run `python -m spot_agent credentials set {environment}`"
        )
    return APICredentials(api_key, api_secret, "Windows Credential Manager")


def store_credentials_interactive(environment: str) -> str:
    import keyring

    service = _service(environment)
    api_key = getpass.getpass("Binance API Key (input hidden): ").strip()
    api_secret = getpass.getpass("Binance Secret Key (input hidden): ").strip()
    if len(api_key) < 16 or len(api_secret) < 16:
        raise ValueError("credentials look too short; nothing was saved")
    keyring.set_password(service, "api_key", api_key)
    keyring.set_password(service, "api_secret", api_secret)
    return f"saved {environment} credentials in Windows Credential Manager"


def delete_credentials(environment: str) -> str:
    import keyring

    service = _service(environment)
    for username in ("api_key", "api_secret"):
        try:
            keyring.delete_password(service, username)
        except keyring.errors.PasswordDeleteError:
            pass
    return f"deleted local {environment} credentials"


def credential_status(environment: str) -> dict[str, str | bool]:
    try:
        credentials = load_credentials(environment)
    except (RuntimeError, ValueError):
        return {"configured": False, "environment": environment}
    key = credentials.api_key
    masked = f"{key[:5]}...{key[-4:]}" if len(key) >= 10 else "configured"
    return {
        "configured": True,
        "environment": environment,
        "api_key": masked,
        "secret": "********",
        "source": credentials.source,
    }

