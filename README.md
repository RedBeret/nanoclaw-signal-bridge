# NanoClaw Signal Agent

A Signal messenger bridge for [NanoClaw](https://github.com/YOUR_USERNAME/nanoclaw) — text your AI agent from anywhere.

> **Not affiliated with Anthropic.** This is a community project that connects Signal to a NanoClaw agent runtime. NanoClaw uses the [claude-code-sdk](https://pypi.org/project/claude-code-sdk/) — see NanoClaw docs for API setup.

## What This Does

Connects your existing NanoClaw agent to Signal messenger so you can interact with it from your phone. That's it.

```
You (Signal) -> signal-cli -> NanoClaw -> Your Agent -> Response -> Signal
```

Your agent:
- Polls Signal for new messages every 5 seconds
- Routes messages through NanoClaw's orchestrator
- Returns the response to you on Signal
- Remembers conversation context across messages
- Can use any tools NanoClaw supports (web, GitHub, file ops, etc.)

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/claude-signal-agent.git
cd claude-signal-agent
./setup
```

The interactive setup wizard walks you through everything.

## Requirements

| Requirement | Notes |
|------------|-------|
| Mac or Linux machine | Dedicated is best — Mac Mini M1 is ideal |
| Python 3.10+ | Usually pre-installed |
| Java 17+ | For signal-cli |
| Anthropic API key or CLI subscription | See [NanoClaw docs](https://github.com/YOUR_USERNAME/nanoclaw) for setup |
| Signal phone number | A second number for your agent (Google Voice works) |

## What's Included

This repo bundles NanoClaw's core runtime stripped to what's needed for Signal integration:

```
src/nanoclaw/
├── cli.py              # CLI commands (daemon, run, chat, status, agents)
├── orchestrator.py     # Session management, rate limit handling
├── agents.py           # Agent definitions, system prompt builder
├── config.py           # Config loader (nanoclaw.json + .env)
├── channels/
│   └── signal.py       # Signal message polling and routing
├── stores/
│   ├── conversations.py  # Encrypted message history (SQLite)
│   ├── crypto.py         # Fernet encryption with Keychain/file key
│   └── usage.py          # Task usage tracking
└── setup/
    └── ...             # Interactive TUI setup wizard (rich + questionary)
```

## CLI

```bash
nanoclaw daemon          # Start the Signal listener
nanoclaw run main "..."  # Run a one-shot task
nanoclaw chat            # Interactive terminal chat
nanoclaw status          # Health check
nanoclaw agents          # List configured agents
nanoclaw setup           # Re-run the setup wizard
```

## Configuration

All config lives in `~/.nanoclaw/`:

| File | Purpose |
|------|---------|
| `nanoclaw.json` | Main config — agents, Signal, MCP servers |
| `.env` | API keys (never committed) |
| `workspace/SOUL.md` | Agent values and hard limits |
| `workspace/IDENTITY.md` | Agent name and persona |
| `workspace/USER.md` | Your profile |
| `workspace/MEMORY.md` | Persistent memory (read/written by agent) |

See `docs/CUSTOMIZATION.md` for the full guide.

## Security

- API keys in `~/.nanoclaw/.env` with `chmod 600`
- Encryption key in macOS Keychain (or restricted file on Linux)
- Conversation history encrypted at rest (Fernet/AES-128-CBC)
- Agent only responds to allowlisted phone numbers
- Pre-commit hook blocks accidental secret commits

## Manual Installation

```bash
pip install -e .
cp config/nanoclaw.json.template ~/.nanoclaw/nanoclaw.json
cp config/identity/*.template ~/.nanoclaw/workspace/
# Edit config, add API key, then:
nanoclaw daemon
```

## License

MIT
