# Architecture

## Overview

NanoClaw Signal Agent is a self-contained agent runtime built on the Anthropic SDK. It provides a Signal messaging interface, persistent memory, encrypted conversation storage, and session management.

## Components

### Orchestrator (`orchestrator.py`)

The core engine. Wraps the SDK to provide:
- Session management (resume conversations across restarts)
- Rate limit detection and notification
- Daily memory logging
- Usage tracking

### Agents (`agents.py`)

Builds system prompts by combining:
1. **SOUL.md** — hard limits and values
2. **IDENTITY.md** — name, persona
3. **USER.md** — user context
4. **Skills** — domain-specific instruction files
5. **MEMORY.md** — persistent memory

Also configures MCP servers (GitHub, Playwright) based on agent skills.

### Signal Channel (`channels/signal.py`)

Polls signal-cli for incoming messages via JSON-RPC. Routes messages through the orchestrator and sends responses back. Maintains an allowlist for security.

### Stores

- **conversations.py** — SQLite message history, encrypted at rest
- **crypto.py** — Fernet encryption with key in macOS Keychain (or file on Linux)
- **usage.py** — Task logging for monitoring

## Data Flow

```
Signal message received
  -> Allowlist check
  -> Retrieve conversation history (encrypted SQLite)
  -> Build prompt with context
  -> Send to LLM via SDK
  -> Stream response
  -> Send reply via Signal
  -> Log to conversation store + daily memory
```

## Adding Features

The architecture is modular. To add a new channel (e.g., Telegram):

1. Create `channels/telegram.py` with an async `run()` method
2. Add config section to `nanoclaw.json`
3. Route from `daemon` command in `cli.py`

To add a new store or tool, create a module in `stores/` or `tools/` and import where needed.
