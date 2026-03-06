"""Step 1: Welcome — detect platform and existing installation."""

import platform
from pathlib import Path

import questionary

from ..ui import step_header, ok, warn, info, console
from ..state import WizardState


def run(state: WizardState):
    step_header(1, "Welcome")

    # Detect platform
    system = platform.system()
    arch = platform.machine()
    if system == "Darwin":
        plat = "mac"
        info(f"Platform: macOS ({arch})")
    elif system == "Linux":
        plat = "linux"
        info(f"Platform: Linux ({arch})")
    else:
        console.print(f"  [err]Unsupported platform: {system}[/err]")
        raise SystemExit(1)

    state.set("platform", plat)

    # Check existing installation
    nanoclaw_home = Path.home() / ".nanoclaw"
    if nanoclaw_home.exists():
        config_exists = (nanoclaw_home / "nanoclaw.json").exists()
        workspace_exists = (nanoclaw_home / "workspace").exists()
        if config_exists:
            ok("Existing ~/.nanoclaw/ directory found")
            if workspace_exists:
                ok("Workspace directory exists")
        else:
            warn("~/.nanoclaw/ exists but no config found")
    else:
        info("Fresh install — will create ~/.nanoclaw/")

    console.print()
    console.print("  This wizard will set up:")
    console.print("    1. Dependencies (Python, Java, signal-cli)")
    console.print("    2. Signal account for your agent")
    console.print("    3. API keys (Anthropic)")
    console.print("    4. Agent identity and personality")
    console.print("    5. Configuration")
    console.print("    6. System service (auto-start)")
    console.print()

    if not questionary.confirm("Ready to begin?", default=True).ask():
        raise SystemExit(0)
