#!/bin/bash
# Claude Signal Agent — Setup Script
# Installs all dependencies to run a personal AI agent with Signal integration
# Run this first, then register-signal.sh, then start.sh

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

info()    { echo -e "${BOLD}[setup]${RESET} $1"; }
success() { echo -e "${GREEN}[  ok  ]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[ warn ]${RESET} $1"; }
error()   { echo -e "${RED}[error ]${RESET} $1"; }

echo ""
echo -e "${BOLD}Claude Signal Agent — Setup${RESET}"
echo "Installs: Homebrew, signal-cli, Python 3, GitHub CLI, workspace structure"
echo ""

# ─── Check OS ─────────────────────────────────────────────────────────────────
if [[ "$(uname)" != "Darwin" ]]; then
  error "This setup script is for macOS. Linux instructions in docs/LINUX.md"
  exit 1
fi

# ─── Homebrew ─────────────────────────────────────────────────────────────────
info "Checking Homebrew..."
if ! command -v brew &>/dev/null; then
  info "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  success "Homebrew installed"
else
  success "Homebrew already installed ($(brew --version | head -1))"
fi

# ─── signal-cli ───────────────────────────────────────────────────────────────
info "Checking signal-cli..."
if ! command -v signal-cli &>/dev/null; then
  info "Installing signal-cli via Homebrew..."
  brew install signal-cli
  success "signal-cli installed ($(signal-cli --version))"
else
  success "signal-cli already installed ($(signal-cli --version))"
fi

# ─── Python ───────────────────────────────────────────────────────────────────
info "Checking Python 3.10+..."
if ! command -v python3 &>/dev/null; then
  info "Installing Python 3..."
  brew install python3
fi
PYTHON_VERSION=$(python3 --version)
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
  success "Python OK ($PYTHON_VERSION)"
else
  error "Python 3.10+ required. Found: $PYTHON_VERSION"
  error "Fix: brew upgrade python3"
  exit 1
fi

# ─── Python venv ──────────────────────────────────────────────────────────────
info "Setting up Python virtual environment..."
NANOCLAW_DIR="$HOME/.nanoclaw"
VENV_DIR="$NANOCLAW_DIR/venv"

if [ -d "$VENV_DIR" ]; then
  warn "venv already exists at $VENV_DIR — skipping creation"
else
  python3 -m venv "$VENV_DIR"
  success "venv created at $VENV_DIR"
fi

info "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
if [ -f "requirements.txt" ]; then
  "$VENV_DIR/bin/pip" install --quiet -r requirements.txt
  success "Python dependencies installed"
else
  warn "requirements.txt not found — skipping pip install"
fi

# ─── GitHub CLI (optional, for coding tasks) ──────────────────────────────────
info "Checking GitHub CLI..."
if ! command -v gh &>/dev/null; then
  info "Installing GitHub CLI..."
  brew install gh
  success "gh installed ($(gh --version | head -1))"
else
  success "gh already installed ($(gh --version | head -1))"
fi

# ─── Directory structure ───────────────────────────────────────────────────────
info "Creating workspace directories..."
mkdir -p "$NANOCLAW_DIR/workspace"/{projects,staging,archive,reports,scripts,memory,docs,templates}
mkdir -p "$NANOCLAW_DIR/logs"
mkdir -p "$NANOCLAW_DIR/sessions"
success "Workspace structure created at $NANOCLAW_DIR/"

# ─── Config ───────────────────────────────────────────────────────────────────
NANOCLAW_CONFIG="$NANOCLAW_DIR/nanoclaw.json"
if [ -f "$NANOCLAW_CONFIG" ]; then
  warn "$NANOCLAW_CONFIG already exists — skipping"
  warn "Edit it manually to update settings"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cp "$SCRIPT_DIR/../config/nanoclaw.json.template" "$NANOCLAW_CONFIG"
  success "Config template copied to $NANOCLAW_CONFIG"
fi

# ─── Identity / Agent Brain ───────────────────────────────────────────────────
# Copies the starter identity files (SOUL.md, IDENTITY.md, USER.md) to ~/.nanoclaw/identity/
# Edit these to personalize your agent.
IDENTITY_DIR="$NANOCLAW_DIR/identity"
if [ -d "$IDENTITY_DIR" ]; then
  warn "$IDENTITY_DIR already exists — skipping"
  warn "Edit ~/.nanoclaw/identity/ to customize your agent's persona"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  mkdir -p "$IDENTITY_DIR"
  for f in SOUL.md IDENTITY.md USER.md; do
    if [ -f "$SCRIPT_DIR/../config/identity/${f}.template" ]; then
      cp "$SCRIPT_DIR/../config/identity/${f}.template" "$IDENTITY_DIR/$f"
    fi
  done
  success "Identity templates copied to $IDENTITY_DIR"
  info "Edit these files to personalize your agent:"
  echo "    $IDENTITY_DIR/IDENTITY.md  — agent name and persona"
  echo "    $IDENTITY_DIR/USER.md      — your profile (how agent knows you)"
  echo "    $IDENTITY_DIR/SOUL.md      — values and hard limits"
fi

# ─── .env setup ───────────────────────────────────────────────────────────────
ENV_FILE="$NANOCLAW_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  warn "$ENV_FILE already exists — skipping"
else
  cat > "$ENV_FILE" << 'EOF'
# Claude API key — get yours at https://console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE

# Optional: Ollama for local model fallback
# OLLAMA_BASE_URL=http://localhost:11434
EOF
  chmod 600 "$ENV_FILE"
  success "Created $ENV_FILE — add your Anthropic API key"
fi

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}Setup complete!${RESET}"
echo ""
echo "Next steps:"
echo "  1. Add your Claude API key:"
echo "        $ENV_FILE"
echo "        ANTHROPIC_API_KEY=sk-ant-..."
echo ""
echo "  2. Register a Signal account for your agent (needs its own number):"
echo "        ./scripts/register-signal.sh"
echo ""
echo "  3. Personalize the agent (optional but recommended):"
echo "        ~/.nanoclaw/identity/IDENTITY.md  — name, persona"
echo "        ~/.nanoclaw/identity/USER.md       — your profile"
echo ""
echo "  4. Start the agent:"
echo "        ./scripts/start.sh"
echo ""
echo "See docs/CUSTOMIZATION.md for full configuration options."
echo ""
