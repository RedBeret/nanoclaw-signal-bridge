#!/bin/bash
# Install Claude Signal Agent as a macOS launchd service (auto-starts on login)

PLIST="$HOME/Library/LaunchAgents/com.claude-signal-agent.plist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$(uname)" != "Darwin" ]; then
    echo "This script is for macOS only. On Linux, use install-systemd.sh"
    exit 1
fi

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.claude-signal-agent</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME/.nanoclaw/scripts/start.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$HOME/.nanoclaw/logs/launchd.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/.nanoclaw/logs/launchd-error.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
</dict>
</plist>
EOF

launchctl load "$PLIST" 2>/dev/null || launchctl bootstrap gui/$(id -u) "$PLIST"

echo "✓ Installed: $PLIST"
echo "✓ Agent will start automatically on login"
echo ""
echo "Manage with:"
echo "  launchctl start com.claude-signal-agent   # start now"
echo "  launchctl stop com.claude-signal-agent    # stop"
echo "  launchctl unload $PLIST  # uninstall"
