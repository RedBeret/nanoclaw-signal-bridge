#!/bin/bash
# Claude Signal Agent — Setup Script
# Installs and configures everything needed to run a Claude agent via Signal.
#
# Run this once on a fresh machine. It's safe to re-run.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC}  $1"; }
err()  { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${BLUE}→${NC} $1"; }

echo ""
echo "======================================"
echo "  Claude Signal Agent — Setup"
echo "======================================"
echo ""

# ─── Detect OS ───────────────────────────────────────────────────────────────

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" = "Darwin" ]; then
    PLATFORM="mac"
    info "Platform: macOS ($ARCH)"
elif [ "$OS" = "Linux" ]; then
    PLATFORM="linux"
    info "Platform: Linux ($ARCH)"
else
    err "Unsupported platform: $OS"
    exit 1
fi

# ─── Check Dependencies ──────────────────────────────────────────────────────

echo ""
info "Checking dependencies..."

# Python 3.10+
if command -v python3 &>/dev/null; then
    PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYMAJ=$(echo $PYVER | cut -d. -f1)
    PYMIN=$(echo $PYVER | cut -d. -f2)
    if [ "$PYMAJ" -ge 3 ] && [ "$PYMIN" -ge 10 ]; then
        ok "Python $PYVER"
    else
        err "Python 3.10+ required (found $PYVER)"
        exit 1
    fi
else
    err "Python 3 not found. Install from python.org"
    exit 1
fi

# Java 17+ (for signal-cli)
if command -v java &>/dev/null; then
    JAVAVER=$(java -version 2>&1 | head -1 | sed 's/.*version "\([0-9]*\).*/\1/')
    if [ "$JAVAVER" -ge 17 ] 2>/dev/null; then
        ok "Java $JAVAVER"
    else
        warn "Java $JAVAVER found — signal-cli requires Java 17+. Install from adoptium.net"
    fi
else
    warn "Java not found — needed for signal-cli. Install from adoptium.net"
fi

# Git
if command -v git &>/dev/null; then
    ok "git $(git --version | awk '{print $3}')"
else
    err "git not found"
    exit 1
fi

# GitHub CLI (optional but recommended)
if command -v gh &>/dev/null; then
    ok "gh (GitHub CLI) — coding tasks enabled"
else
    warn "gh (GitHub CLI) not found — GitHub tasks will be disabled. Install: brew install gh"
fi

# ─── Create Directory Structure ───────────────────────────────────────────────

echo ""
info "Creating ~/.nanoclaw directory structure..."

mkdir -p ~/.nanoclaw/{workspace,logs,agents,identity,scripts}
mkdir -p ~/.nanoclaw/workspace/{memory,skills,projects,staging}

ok "Directories created"

# ─── Python Virtual Environment ──────────────────────────────────────────────

echo ""
info "Setting up Python environment..."

if [ ! -d ~/.nanoclaw/venv ]; then
    python3 -m venv ~/.nanoclaw/venv
    ok "Virtual environment created"
else
    ok "Virtual environment already exists"
fi

source ~/.nanoclaw/venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet -r "$(dirname "$0")/requirements.txt"
ok "Python packages installed"

# ─── signal-cli ──────────────────────────────────────────────────────────────

echo ""
info "Checking signal-cli..."

SIGNAL_CLI_VERSION="0.13.24"

if command -v signal-cli &>/dev/null; then
    ok "signal-cli already installed ($(signal-cli --version | head -1))"
else
    info "Installing signal-cli $SIGNAL_CLI_VERSION..."

    if [ "$PLATFORM" = "mac" ]; then
        if command -v brew &>/dev/null; then
            brew install signal-cli 2>/dev/null && ok "signal-cli installed via Homebrew" || {
                warn "Homebrew install failed — trying manual install"
                install_signal_cli_manual
            }
        else
            install_signal_cli_manual
        fi
    else
        install_signal_cli_manual
    fi
fi

install_signal_cli_manual() {
    # Download the native build for the current platform
    if [ "$PLATFORM" = "mac" ] && [ "$ARCH" = "arm64" ]; then
        URL="https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}-macOS-aarch64.tar.gz"
    elif [ "$PLATFORM" = "mac" ]; then
        URL="https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}-macOS-x86_64.tar.gz"
    else
        URL="https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}-Linux-native.tar.gz"
    fi

    echo "  Downloading from: $URL"
    curl -fsSL "$URL" -o /tmp/signal-cli.tar.gz
    tar -xzf /tmp/signal-cli.tar.gz -C /tmp
    sudo mv /tmp/signal-cli-*/bin/signal-cli /usr/local/bin/
    rm -rf /tmp/signal-cli*
    ok "signal-cli installed to /usr/local/bin/"
}

# ─── Signal Account Registration ─────────────────────────────────────────────

echo ""
echo "======================================"
echo "  Signal Account Setup"
echo "======================================"
echo ""
echo "Your agent needs its own Signal account."
echo "This must be a real phone number (not your personal Signal)."
echo "Options: a second SIM, a VoIP number (Google Voice, Twilio), etc."
echo ""
read -p "Enter the phone number for your AGENT (e.g. +15555551234): " AGENT_NUMBER

if [ -z "$AGENT_NUMBER" ]; then
    warn "No number provided — skipping Signal registration. Run setup.sh again to complete."
else
    echo ""
    info "Requesting verification code for $AGENT_NUMBER..."
    signal-cli -a "$AGENT_NUMBER" register --voice || signal-cli -a "$AGENT_NUMBER" register

    echo ""
    read -p "Enter the verification code you received: " VERIFY_CODE

    if [ -n "$VERIFY_CODE" ]; then
        signal-cli -a "$AGENT_NUMBER" verify "$VERIFY_CODE"
        ok "Signal account registered: $AGENT_NUMBER"
    fi
fi

# ─── Copy Config Templates ────────────────────────────────────────────────────

echo ""
info "Setting up configuration templates..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f ~/.nanoclaw/nanoclaw.json ]; then
    cp "$SCRIPT_DIR/config/nanoclaw.json.template" ~/.nanoclaw/nanoclaw.json
    # Inject the agent number if we have it
    if [ -n "$AGENT_NUMBER" ]; then
        sed -i.bak "s/YOUR_AGENT_NUMBER/$AGENT_NUMBER/g" ~/.nanoclaw/nanoclaw.json
        rm -f ~/.nanoclaw/nanoclaw.json.bak
    fi
    ok "nanoclaw.json created — edit to finish configuration"
else
    ok "nanoclaw.json already exists — skipping"
fi

for f in SOUL IDENTITY USER; do
    if [ ! -f ~/.nanoclaw/workspace/${f}.md ]; then
        cp "$SCRIPT_DIR/config/identity/${f}.md.template" ~/.nanoclaw/workspace/${f}.md
        ok "${f}.md created"
    else
        ok "${f}.md already exists — skipping"
    fi
done

if [ ! -f ~/.nanoclaw/workspace/MEMORY.md ]; then
    cp "$SCRIPT_DIR/workspace/MEMORY.md.template" ~/.nanoclaw/workspace/MEMORY.md
    ok "MEMORY.md created"
fi

# ─── .env Setup ──────────────────────────────────────────────────────────────

echo ""
info "Setting up .env file..."

if [ ! -f ~/.nanoclaw/.env ]; then
    cat > ~/.nanoclaw/.env << 'ENVEOF'
# Claude Signal Agent — Environment Variables
# KEEP THIS FILE PRIVATE. Never commit it.

ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
ENVEOF
    chmod 600 ~/.nanoclaw/.env
    ok ".env created — add your Anthropic API key"
else
    ok ".env already exists — skipping"
fi

# ─── Install scripts ──────────────────────────────────────────────────────────

cp "$SCRIPT_DIR/scripts/"*.sh ~/.nanoclaw/scripts/
chmod +x ~/.nanoclaw/scripts/*.sh
ok "Scripts installed to ~/.nanoclaw/scripts/"

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "======================================"
echo "  Setup Complete"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Add your Anthropic API key:"
echo "     nano ~/.nanoclaw/.env"
echo ""
echo "  2. Edit your identity files:"
echo "     nano ~/.nanoclaw/workspace/IDENTITY.md"
echo "     nano ~/.nanoclaw/workspace/USER.md"
echo ""
echo "  3. Edit your config (add your number, allowlist your personal number):"
echo "     nano ~/.nanoclaw/nanoclaw.json"
echo ""
echo "  4. Start your agent:"
echo "     ~/.nanoclaw/scripts/start.sh"
echo ""
echo "  5. Message your agent on Signal — it should respond."
echo ""
