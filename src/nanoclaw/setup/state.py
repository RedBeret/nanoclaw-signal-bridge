"""Wizard state persistence — tracks completed steps and collected values."""

import json
from datetime import datetime
from pathlib import Path

STATE_PATH = Path.home() / ".nanoclaw" / ".setup-state.json"

STEPS = [
    "welcome",
    "dependencies",
    "signal_setup",
    "api_keys",
    "identity",
    "agent_config",
    "service",
    "health",
]


class WizardState:
    def __init__(self):
        self.completed: list[str] = []
        self.values: dict = {}
        self.started_at: str = datetime.now().isoformat()
        self._load()

    def _load(self):
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text())
                self.completed = data.get("completed_steps", [])
                self.values = data.get("values", {})
                self.started_at = data.get("started_at", self.started_at)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps({
            "version": 1,
            "completed_steps": self.completed,
            "values": self.values,
            "started_at": self.started_at,
            "last_updated": datetime.now().isoformat(),
        }, indent=2))

    def mark_done(self, step: str):
        if step not in self.completed:
            self.completed.append(step)
        self.save()

    def is_done(self, step: str) -> bool:
        return step in self.completed

    def set(self, key: str, value):
        self.values[key] = value
        self.save()

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    @property
    def next_step(self) -> str | None:
        for step in STEPS:
            if step not in self.completed:
                return step
        return None

    @property
    def has_prior_run(self) -> bool:
        return STATE_PATH.exists() and len(self.completed) > 0

    def reset(self):
        self.completed = []
        self.values = {}
        self.started_at = datetime.now().isoformat()
        self.save()
