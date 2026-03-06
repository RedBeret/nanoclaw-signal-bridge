"""Step 4: API key configuration."""

import os
import shutil
from pathlib import Path

import questionary

from ..ui import step_header, ok, warn, info, console
from ..state import WizardState

ENV_PATH = Path.home() / ".nanoclaw" / ".env"


def run(state: WizardState):
    step_header(4, "API Keys")

    auth_mode = questionary.select(
        "How will you authenticate with the Anthropic API?",
        choices=[
            "Anthropic API key (pay per token)",
            "Anthropic CLI subscription (if you have the CLI installed)",
        ],
    ).ask()

    if "API key" in auth_mode:
        # Check existing
        if ENV_PATH.exists():
            existing = ENV_PATH.read_text()
            if "ANTHROPIC_API_KEY" in existing and "YOUR_KEY_HERE" not in existing:
                ok("API key already configured in ~/.nanoclaw/.env")
                if not questionary.confirm("Replace it?", default=False).ask():
                    state.set("auth_mode", "api_key")
                    return

        api_key = questionary.password(
            "Anthropic API key (from console.anthropic.com):",
            validate=lambda k: k.startswith("sk-ant-") or "Key should start with sk-ant-",
        ).ask()

        if not api_key:
            warn("No key provided. Add it later to ~/.nanoclaw/.env")
            state.set("auth_mode", "api_key")
            return

        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        ENV_PATH.write_text(
            f"# NanoClaw Signal Agent — API Key\n"
            f"# Keep this file private. Never commit it.\n"
            f"ANTHROPIC_API_KEY={api_key}\n"
        )
        ENV_PATH.chmod(0o600)
        ok("API key saved to ~/.nanoclaw/.env (permissions: 600)")
        state.set("auth_mode", "api_key")

    else:
        # Subscription mode
        if shutil.which("claude"):
            ok("Anthropic CLI found — will use subscription authentication")
        else:
            warn("Anthropic CLI not found. Install it first:")
            info("  npm install -g @anthropic-ai/claude-code")
            info("  claude login")
        state.set("auth_mode", "subscription")

    # Ensure .env exists even for subscription mode
    if not ENV_PATH.exists():
        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        ENV_PATH.write_text("# NanoClaw Signal Agent — Environment\n")
        ENV_PATH.chmod(0o600)
