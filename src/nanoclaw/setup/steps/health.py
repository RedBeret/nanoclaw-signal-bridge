"""Step 8: Final health check — verify everything works."""

import json
import shutil
from pathlib import Path

from ..ui import step_header, ok, warn, err, status_table, done_panel, console
from ..state import WizardState

NANOCLAW_HOME = Path.home() / ".nanoclaw"


def run(state: WizardState):
    step_header(8, "Health Check")

    checks = []

    # Config
    config_path = NANOCLAW_HOME / "nanoclaw.json"
    if config_path.exists():
        try:
            json.loads(config_path.read_text())
            checks.append(("nanoclaw.json", "valid", "ok"))
        except json.JSONDecodeError:
            checks.append(("nanoclaw.json", "invalid JSON", "fix manually"))
    else:
        checks.append(("nanoclaw.json", "missing", "run setup again"))

    # .env
    env_path = NANOCLAW_HOME / ".env"
    if env_path.exists():
        content = env_path.read_text()
        if "ANTHROPIC_API_KEY" in content and "YOUR_KEY_HERE" not in content:
            checks.append(("API key", "configured", "ok"))
        else:
            auth_mode = state.get("auth_mode", "")
            if auth_mode == "subscription":
                checks.append(("API key", "subscription mode", "ok"))
            else:
                checks.append(("API key", "placeholder", "add your key to ~/.nanoclaw/.env"))
    else:
        checks.append(("API key", "no .env file", "run setup step 4"))

    # signal-cli
    if shutil.which("signal-cli"):
        checks.append(("signal-cli", "installed", "ok"))
    else:
        checks.append(("signal-cli", "not found", "install for Signal features"))

    # Identity files
    ws = NANOCLAW_HOME / "workspace"
    for fname in ("SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md"):
        fpath = ws / fname
        if fpath.exists():
            checks.append((fname, "found", "ok"))
        else:
            checks.append((fname, "missing", "run setup step 5"))

    # Workspace dirs
    dirs_ok = all(
        (ws / d).is_dir()
        for d in ("memory", "skills", "projects")
    )
    if dirs_ok:
        checks.append(("Workspace dirs", "ok", "ok"))
    else:
        checks.append(("Workspace dirs", "incomplete", "run setup step 2"))

    # gh CLI
    if shutil.which("gh"):
        checks.append(("gh CLI", "installed", "ok"))
    else:
        checks.append(("gh CLI", "not found", "optional"))

    # nanoclaw CLI
    if shutil.which("nanoclaw"):
        checks.append(("nanoclaw CLI", "installed", "ok"))
    else:
        checks.append(("nanoclaw CLI", "not in PATH", "run: pip install -e ."))

    status_table(checks)

    # Count issues
    issues = [c for c in checks if c[2] != "ok" and c[2] != "optional"]
    if issues:
        console.print()
        warn(f"{len(issues)} issue(s) found — see table above")
    else:
        done_panel([
            "All checks passed!",
            "",
            "Start your agent:",
            "  nanoclaw daemon",
            "",
            "Or run a quick test:",
            "  nanoclaw run main \"Hello, are you there?\"",
            "",
            "Interactive chat:",
            "  nanoclaw chat",
            "",
            "Docs: docs/CUSTOMIZATION.md",
        ])
