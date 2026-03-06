"""Configuration loader for NanoClaw."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv


NANOCLAW_HOME = Path(os.environ.get("NANOCLAW_HOME", Path.home() / ".nanoclaw"))


def resolve_path(p: str) -> Path:
    """Resolve ~ and relative paths against NANOCLAW_HOME."""
    return Path(os.path.expanduser(p))


class Config:
    """Loads nanoclaw.json and .env, provides typed access."""

    def __init__(self, home: Path | None = None):
        self.home = home or NANOCLAW_HOME
        self._data: dict = {}
        self.load()

    def load(self):
        env_path = self.home / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        config_path = self.home / "nanoclaw.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        self._data = json.loads(config_path.read_text())

    @property
    def raw(self) -> dict:
        return self._data

    @property
    def agents_defaults(self) -> dict:
        return self._data.get("agents", {}).get("defaults", {})

    @property
    def agents_list(self) -> dict:
        return self._data.get("agents", {}).get("list", {})

    @property
    def channels(self) -> dict:
        return self._data.get("channels", {})

    @property
    def signal_config(self) -> dict | None:
        sig = self.channels.get("signal", {})
        return sig if sig.get("enabled") else None

    @property
    def nodes(self) -> dict:
        return self._data.get("nodes", {})

    def path(self, key: str) -> Path:
        paths = self._data.get("paths", {})
        raw = paths.get(key, str(self.home / key))
        return resolve_path(raw)

    @property
    def workspace(self) -> Path:
        return self.path("workspace")

    @property
    def auth_mode(self) -> str:
        if os.environ.get("ANTHROPIC_API_KEY"):
            return "api_key"
        return "subscription"
