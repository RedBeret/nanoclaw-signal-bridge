"""Step 2: Check and install dependencies."""

import shutil
import subprocess
import sys

import questionary

from ..ui import step_header, ok, warn, err, info, status_table
from ..state import WizardState


def _check_python() -> tuple[str, str]:
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        return ver, "ok"
    return ver, "too old (need 3.10+)"


def _check_java() -> tuple[str, str]:
    try:
        result = subprocess.run(
            ["java", "-version"], capture_output=True, text=True, timeout=5,
        )
        output = result.stderr or result.stdout
        import re
        match = re.search(r'version "(\d+)', output)
        if match:
            ver = match.group(1)
            if int(ver) >= 17:
                return ver, "ok"
            return ver, "too old (need 17+)"
        return "unknown", "check manually"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "not found", "missing"


def _check_signal_cli() -> tuple[str, str]:
    try:
        result = subprocess.run(
            ["signal-cli", "--version"], capture_output=True, text=True, timeout=5,
        )
        ver = result.stdout.strip().split()[-1] if result.stdout.strip() else "installed"
        return ver, "ok"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "not found", "missing"


def _check_gh() -> tuple[str, str]:
    try:
        result = subprocess.run(
            ["gh", "--version"], capture_output=True, text=True, timeout=5,
        )
        ver = result.stdout.strip().split("\n")[0].split()[-1] if result.stdout else "installed"
        # Check auth
        auth = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, timeout=5,
        )
        if auth.returncode == 0:
            return ver, "ok (authenticated)"
        return ver, "ok (not authenticated)"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "not found", "optional"


def _check_claude_cli() -> tuple[str, str]:
    if shutil.which("claude"):
        return "installed", "ok"
    return "not found", "optional"


def _install_with_brew(package: str) -> bool:
    if not shutil.which("brew"):
        return False
    info(f"Installing {package} via Homebrew...")
    result = subprocess.run(
        ["brew", "install", package],
        capture_output=False,
        timeout=300,
    )
    return result.returncode == 0


def run(state: WizardState):
    step_header(2, "Dependencies")

    plat = state.get("platform", "mac")

    python_ver, python_status = _check_python()
    java_ver, java_status = _check_java()
    signal_ver, signal_status = _check_signal_cli()
    gh_ver, gh_status = _check_gh()
    claude_ver, claude_status = _check_claude_cli()

    rows = [
        ("Python 3.10+", f"{python_ver}", "ok" if python_status == "ok" else python_status),
        ("Java 17+", f"{java_ver}", "ok" if java_status == "ok" else java_status),
        ("signal-cli", f"{signal_ver}", "ok" if signal_status == "ok" else "will install" if plat == "mac" else "install manually"),
        ("gh CLI", f"{gh_ver}", "ok" if "ok" in gh_status else "optional — GitHub features"),
        ("Anthropic CLI", f"{claude_ver}", "ok" if claude_status == "ok" else "optional — subscription auth"),
    ]
    status_table(rows)

    # Install missing required deps
    if python_status != "ok":
        err("Python 3.10+ is required. Install from python.org and re-run setup.")
        raise SystemExit(1)

    if java_status == "missing":
        if plat == "mac" and questionary.confirm("Install Java via Homebrew?", default=True).ask():
            if _install_with_brew("openjdk"):
                ok("Java installed")
            else:
                warn("Install failed. Install manually: brew install openjdk")
        else:
            warn("Install Java 17+ manually. signal-cli requires it.")
            warn("  macOS: brew install openjdk")
            warn("  Linux: sudo apt install openjdk-17-jre")

    if signal_status == "missing":
        if plat == "mac" and questionary.confirm("Install signal-cli via Homebrew?", default=True).ask():
            if _install_with_brew("signal-cli"):
                ok("signal-cli installed")
            else:
                err("Install failed. Install manually: brew install signal-cli")
        else:
            warn("Install signal-cli manually:")
            warn("  macOS: brew install signal-cli")
            warn("  Linux: https://github.com/AsamK/signal-cli/releases")
            if not questionary.confirm("Continue without signal-cli?", default=False).ask():
                raise SystemExit(1)

    if "not authenticated" in gh_status:
        info("Run 'gh auth login' later to enable GitHub features.")

    # Create directory structure
    info("Creating ~/.nanoclaw/ directory structure...")
    from pathlib import Path
    home = Path.home() / ".nanoclaw"
    for d in ["workspace/memory", "workspace/skills", "workspace/projects",
              "logs", "agents", "identity", "scripts"]:
        (home / d).mkdir(parents=True, exist_ok=True)
    ok("Directory structure created")
