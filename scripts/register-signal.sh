#!/bin/bash
# Register a Signal account for your agent
# Run this once after setup.sh

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

info()    { echo -e "${BOLD}[signal]${RESET} $1"; }
success() { echo -e "${GREEN}[  ok  ]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[ warn ]${RESET} $1"; }
error()   { echo -e "${RED}[error ]${RESET} $1"; }

echo ""
echo -e "${BOLD}Signal Account Registration${RESET}"
echo "The agent needs its own Signal account (separate from yours)."
echo ""
echo "Options for the agent's phone number:"
echo "  - Google Voice number (free at voice.google.com)"
echo "  - A cheap prepaid SIM"
echo "  - Any VoIP number that can receive SMS"
echo ""

read -rp "Enter the agent's phone number (e.g. +12125551234): " AGENT_NUMBER

if [[ ! "$AGENT_NUMBER" =~ ^\+[0-9]{10,15}$ ]]; then
  error "Invalid phone number format. Use international format: +12125551234"
  exit 1
fi

info "Checking signal-cli..."
if ! command -v signal-cli &>/dev/null; then
  error "signal-cli not found. Run ./scripts/setup.sh first."
  exit 1
fi

info "Registering $AGENT_NUMBER with Signal..."
echo ""
warn "Signal will send a verification code via SMS to $AGENT_NUMBER"
echo ""
read -rp "Press Enter to request the verification code..."

signal-cli -a "$AGENT_NUMBER" register

echo ""
read -rp "Enter the verification code Signal sent: " VERIFY_CODE
VERIFY_CODE=$(echo "$VERIFY_CODE" | tr -d ' -')

info "Verifying..."
signal-cli -a "$AGENT_NUMBER" verify "$VERIFY_CODE"

success "Signal account registered for $AGENT_NUMBER"
echo ""

# Update nanoclaw.json with the number
NANOCLAW_CONFIG="$HOME/.nanoclaw/nanoclaw.json"
if [ -f "$NANOCLAW_CONFIG" ]; then
  info "Updating ~/.nanoclaw/nanoclaw.json with agent number..."
  # Use Python for safe JSON editing
  python3 - <<PYTHON
import json, re

with open('$NANOCLAW_CONFIG', 'r') as f:
    config = json.load(f)

config['channels']['signal']['account'] = '$AGENT_NUMBER'

with open('$NANOCLAW_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)

print("  Updated nanoclaw.json")
PYTHON
fi

echo ""
echo -e "${GREEN}${BOLD}Signal setup complete!${RESET}"
echo ""
echo "Agent number: $AGENT_NUMBER"
echo ""
echo "Next: Add YOUR phone number to the allowlist in ~/.nanoclaw/nanoclaw.json:"
echo '  "allowlist": ["YOUR_NUMBER_HERE"]'
echo ""
echo "Then run: ./scripts/start.sh"
echo ""
