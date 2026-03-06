"""Step 6: Agent configuration — model, allowlist, features."""

import json
import re
from pathlib import Path

import questionary

from ..ui import step_header, ok, warn, info, console
from ..state import WizardState

CONFIG_PATH = Path.home() / ".nanoclaw" / "nanoclaw.json"


def run(state: WizardState):
    step_header(6, "Configuration")

    if CONFIG_PATH.exists():
        ok("nanoclaw.json already exists")
        if not questionary.confirm("Regenerate configuration?", default=False).ask():
            return

    model = questionary.select(
        "Primary model:",
        choices=[
            "claude-sonnet-4-6 (recommended — fast + capable)",
            "claude-haiku-4-5 (fastest — lower cost)",
            "claude-opus-4-6 (most capable — slower)",
        ],
    ).ask()
    model_id = model.split(" ")[0]

    agent_number = state.get("agent_number", "+1XXXXXXXXXX")
    user_number = ""

    if not state.get("signal_skipped"):
        user_number = questionary.text(
            "Your phone number (for Signal allowlist, e.g. +15555551234):",
            validate=lambda n: bool(re.match(r'^\+\d{10,15}$', n)) or "Use international format",
        ).ask() or ""

    features = questionary.checkbox(
        "Enable optional features:",
        choices=[
            questionary.Choice("GitHub integration (requires gh CLI)", checked=True),
            questionary.Choice("Web browsing (Playwright MCP)", checked=False),
        ],
    ).ask() or []

    agent_name = state.get("agent_name", "Agent")

    # Build config
    config = {
        "version": 1,
        "name": agent_name.lower(),
        "agents": {
            "defaults": {
                "model": model_id,
                "max_turns": 50,
                "permission_mode": "acceptEdits",
            },
            "list": {
                "main": {
                    "model": model_id,
                    "description": "General-purpose assistant",
                    "skills": ["coding", "research", "writing", "sysadmin",
                               "github", "web-browsing", "automation",
                               "debugging", "deployment"],
                    "tools": ["Read", "Write", "Edit", "Bash", "Glob",
                              "Grep", "WebSearch", "WebFetch"],
                    "workspace": "~/.nanoclaw/workspace",
                },
                "coder": {
                    "model": model_id,
                    "description": "Code-focused agent",
                    "skills": ["coding", "github", "testing", "debugging"],
                    "tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
                    "workspace": "~/.nanoclaw/workspace",
                },
            },
        },
        "channels": {
            "signal": {
                "enabled": not state.get("signal_skipped", False),
                "account": agent_number,
                "allowlist": [user_number] if user_number else [],
                "poll_interval_seconds": 5,
                "daemon_port": 19756,
            },
        },
        "nodes": {},
        "mcp_servers": {},
        "paths": {
            "workspace": "~/.nanoclaw/workspace",
            "logs": "~/.nanoclaw/logs",
            "sessions": "~/.nanoclaw/agents",
            "identity": "~/.nanoclaw/identity",
            "scripts": "~/.nanoclaw/scripts",
        },
    }

    if "GitHub" in str(features):
        config["mcp_servers"]["github"] = {
            "type": "http",
            "url": "https://api.githubcopilot.com/mcp/",
            "auth": "gh_cli",
            "enabled_for_skills": ["github", "coding"],
        }

    if "Playwright" in str(features):
        config["mcp_servers"]["playwright"] = {
            "type": "stdio",
            "command": "npx",
            "args": ["@playwright/mcp@latest"],
            "enabled_for_skills": ["web-browsing", "testing"],
        }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    ok(f"Configuration written to {CONFIG_PATH}")

    # Summary
    console.print()
    info(f"Model: {model_id}")
    info(f"Agents: {', '.join(config['agents']['list'].keys())}")
    if config["channels"]["signal"]["enabled"]:
        info(f"Signal: enabled (agent: {agent_number})")
    else:
        info("Signal: disabled (no number configured)")
    if config["mcp_servers"]:
        info(f"MCP servers: {', '.join(config['mcp_servers'].keys())}")
