"""Step 3: Signal account registration."""

import re
import shutil
import subprocess
from pathlib import Path

import questionary

from ..ui import step_header, ok, warn, err, info, console
from ..state import WizardState


def _signal_account_exists(number: str) -> bool:
    """Check if a Signal account is already registered."""
    data_dir = Path.home() / ".local" / "share" / "signal-cli" / "data"
    if data_dir.exists():
        for f in data_dir.iterdir():
            if number.lstrip("+") in f.name:
                return True
    return False


def run(state: WizardState):
    step_header(3, "Signal Account")

    if not shutil.which("signal-cli"):
        warn("signal-cli not installed — skipping Signal registration.")
        warn("Install it later and re-run setup.")
        state.set("signal_skipped", True)
        return

    console.print("  Your agent needs its own Signal account.")
    console.print("  This must be a [bold]separate[/bold] phone number from yours.")
    console.print()
    console.print("  Options for the agent's number:")
    console.print("    - Google Voice (free at voice.google.com)")
    console.print("    - A cheap prepaid SIM")
    console.print("    - Any VoIP number that can receive SMS/calls")
    console.print()

    number = questionary.text(
        "Agent's phone number (e.g. +15555551234):",
        validate=lambda n: bool(re.match(r'^\+\d{10,15}$', n)) or "Use international format: +15555551234",
    ).ask()

    if not number:
        warn("No number provided — skipping Signal registration.")
        state.set("signal_skipped", True)
        return

    state.set("agent_number", number)

    # Check if already registered
    if _signal_account_exists(number):
        ok(f"Signal account already registered: {number}")
        return

    # Register
    method = questionary.select(
        "Verification method:",
        choices=["Voice call", "SMS"],
    ).ask()

    info(f"Requesting verification for {number}...")
    cmd = ["signal-cli", "-a", number, "register"]
    if method == "Voice call":
        cmd.append("--voice")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        err(f"Registration failed: {result.stderr.strip()}")
        warn("You can register manually later: signal-cli -a YOUR_NUMBER register")
        return

    code = questionary.text(
        "Enter the verification code:",
        validate=lambda c: bool(re.match(r'^\d{3,8}$', c.replace("-", "").replace(" ", "")))
            or "Enter the numeric code",
    ).ask()

    if not code:
        warn("No code provided — skipping verification.")
        return

    code = code.replace("-", "").replace(" ", "")
    result = subprocess.run(
        ["signal-cli", "-a", number, "verify", code],
        capture_output=True, text=True, timeout=15,
    )

    if result.returncode == 0:
        ok(f"Signal account registered: {number}")
    else:
        err(f"Verification failed: {result.stderr.strip()}")
        warn("Try again later with: signal-cli -a YOUR_NUMBER register")
