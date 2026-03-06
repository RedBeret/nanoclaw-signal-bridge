#!/bin/bash
# Start the Claude Signal Agent

NANOCLAW_DIR="$HOME/.nanoclaw"
LOG_FILE="$NANOCLAW_DIR/logs/nanoclaw.log"
ENV_FILE="$NANOCLAW_DIR/.env"

# Load environment
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "ERROR: .env not found at $ENV_FILE"
    echo "Copy the template and add your API key:"
    echo "  cp config/nanoclaw.json.template ~/.nanoclaw/.env"
    exit 1
fi

# Check API key is set
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "sk-ant-YOUR_KEY_HERE" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set in $ENV_FILE"
    echo "Add your key from console.anthropic.com"
    exit 1
fi

# Create log dir
mkdir -p "$NANOCLAW_DIR/logs"

echo "Starting Claude Signal Agent..."
echo "Logs: $LOG_FILE"
echo "Press Ctrl+C to stop."
echo ""

source "$NANOCLAW_DIR/venv/bin/activate"

# Start NanoClaw
nanoclaw start 2>&1 | tee -a "$LOG_FILE"
