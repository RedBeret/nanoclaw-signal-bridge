#!/bin/bash
# Claude Signal Agent — Health Check

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1"; FAILED=1; }
warn() { echo -e "${YELLOW}⚠${NC}  $1"; }

FAILED=0
NANOCLAW_DIR="$HOME/.nanoclaw"

echo "Claude Signal Agent — Health Check"
echo "==================================="
echo ""

# Python/venv
if [ -f "$NANOCLAW_DIR/venv/bin/python3" ]; then
    ok "Python venv exists"
else
    err "Python venv not found — run setup.sh"
fi

# API key set
if [ -f "$NANOCLAW_DIR/.env" ]; then
    source "$NANOCLAW_DIR/.env" 2>/dev/null
    if [ -n "$ANTHROPIC_API_KEY" ] && [ "$ANTHROPIC_API_KEY" != "sk-ant-YOUR_KEY_HERE" ]; then
        ok "Anthropic API key set"
    else
        err "Anthropic API key not configured in ~/.nanoclaw/.env"
    fi
else
    err ".env file not found"
fi

# signal-cli
if command -v signal-cli &>/dev/null; then
    ok "signal-cli installed ($(signal-cli --version | head -1))"
else
    err "signal-cli not found — run setup.sh"
fi

# signal-cli daemon
if curl -s -X POST http://127.0.0.1:19756/api/v1/rpc \
    -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","method":"listAccounts","params":{},"id":1}' \
    &>/dev/null; then
    ok "signal-cli daemon responding"
else
    warn "signal-cli daemon not running (start agent first)"
fi

# Config file
if [ -f "$NANOCLAW_DIR/nanoclaw.json" ]; then
    ok "nanoclaw.json exists"
    # Check if placeholders remain
    if grep -q "YOUR_" "$NANOCLAW_DIR/nanoclaw.json"; then
        warn "nanoclaw.json still has YOUR_* placeholders — finish configuration"
    fi
else
    err "nanoclaw.json not found — run setup.sh"
fi

# Identity files
for f in SOUL IDENTITY USER MEMORY; do
    if [ -f "$NANOCLAW_DIR/workspace/${f}.md" ]; then
        ok "${f}.md exists"
    else
        err "${f}.md missing — run setup.sh"
    fi
done

# Disk space
FREE_GB=$(df -g "$HOME" 2>/dev/null | awk 'NR==2{print $4}' || df -BG "$HOME" 2>/dev/null | awk 'NR==2{gsub("G",""); print $4}')
if [ -n "$FREE_GB" ]; then
    if [ "$FREE_GB" -lt 5 ]; then
        warn "Low disk space: ${FREE_GB}GB free"
    else
        ok "Disk space: ${FREE_GB}GB free"
    fi
fi

# gh CLI
if command -v gh &>/dev/null; then
    if gh auth status &>/dev/null; then
        GH_USER=$(gh api user -q .login 2>/dev/null)
        ok "GitHub CLI authenticated as: $GH_USER"
    else
        warn "gh CLI installed but not authenticated (run: gh auth login)"
    fi
else
    warn "gh CLI not installed — GitHub tasks unavailable"
fi

echo ""
echo "==================================="
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}All checks passed${NC}"
else
    echo -e "${RED}Issues found — address errors above${NC}"
    exit 1
fi
