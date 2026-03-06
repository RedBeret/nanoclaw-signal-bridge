#!/bin/bash
# Install Claude Signal Agent as a Linux systemd user service

if [ "$(uname)" != "Linux" ]; then
    echo "This script is for Linux only. On macOS, use install-launchd.sh"
    exit 1
fi

SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/claude-signal-agent.service"

mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Claude Signal Agent
After=network.target

[Service]
Type=simple
ExecStart=$HOME/.nanoclaw/scripts/start.sh
Restart=always
RestartSec=10
StandardOutput=append:$HOME/.nanoclaw/logs/systemd.log
StandardError=append:$HOME/.nanoclaw/logs/systemd-error.log
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable claude-signal-agent
systemctl --user start claude-signal-agent

echo "✓ Service installed and started"
echo ""
echo "Manage with:"
echo "  systemctl --user status claude-signal-agent"
echo "  systemctl --user stop claude-signal-agent"
echo "  systemctl --user restart claude-signal-agent"
echo "  journalctl --user -u claude-signal-agent -f   # live logs"
