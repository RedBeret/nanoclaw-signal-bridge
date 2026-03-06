"""Step 7: System service installation (LaunchAgent / systemd)."""

import os
import shutil
import subprocess
from pathlib import Path

import questionary

from ..ui import step_header, ok, warn, info, console
from ..state import WizardState


def _install_launchd(nanoclaw_bin: str):
    """Install macOS LaunchAgent."""
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.nanoclaw.daemon.plist"

    home = str(Path.home())
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nanoclaw.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>{nanoclaw_bin}</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>{home}/.nanoclaw/logs/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>{home}/.nanoclaw/logs/daemon.err.log</string>
    <key>WorkingDirectory</key>
    <string>{home}/.nanoclaw/workspace</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>{home}</string>
        <key>PATH</key>
        <string>{home}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>"""

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist)

    # Bootstrap with launchctl
    uid = os.getuid()
    subprocess.run(
        ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
        capture_output=True,
    )
    ok(f"LaunchAgent installed: {plist_path}")
    info("Agent will start automatically on login")
    console.print()
    info("Manage with:")
    info(f"  launchctl kickstart gui/{uid}/com.nanoclaw.daemon")
    info(f"  launchctl kill SIGTERM gui/{uid}/com.nanoclaw.daemon")


def _install_systemd(nanoclaw_bin: str):
    """Install Linux systemd user service."""
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_path = service_dir / "nanoclaw.service"

    home = str(Path.home())
    service = f"""[Unit]
Description=NanoClaw Signal Agent
After=network.target

[Service]
Type=simple
ExecStart={nanoclaw_bin} daemon
Restart=always
RestartSec=10
StandardOutput=append:{home}/.nanoclaw/logs/systemd.log
StandardError=append:{home}/.nanoclaw/logs/systemd-error.log
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=default.target"""

    service_dir.mkdir(parents=True, exist_ok=True)
    service_path.write_text(service)

    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    subprocess.run(["systemctl", "--user", "enable", "nanoclaw"], capture_output=True)

    ok(f"Systemd service installed: {service_path}")
    info("Manage with:")
    info("  systemctl --user start nanoclaw")
    info("  systemctl --user status nanoclaw")
    info("  journalctl --user -u nanoclaw -f")


def run(state: WizardState):
    step_header(7, "System Service")

    plat = state.get("platform", "mac")
    nanoclaw_bin = shutil.which("nanoclaw") or str(Path.home() / ".local" / "bin" / "nanoclaw")

    if plat == "mac":
        if questionary.confirm("Install as macOS LaunchAgent (auto-starts on login)?", default=True).ask():
            _install_launchd(nanoclaw_bin)
        else:
            info("Skipped. Start manually with: nanoclaw daemon")
    else:
        if questionary.confirm("Install as systemd user service?", default=True).ask():
            _install_systemd(nanoclaw_bin)
        else:
            info("Skipped. Start manually with: nanoclaw daemon")
