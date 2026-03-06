# Claude Signal Agent

A self-hosted Claude AI agent you control via Signal messenger — running on your own hardware, 24/7.

Ask it questions, run tasks, build tools, manage your GitHub, browse the web. All from Signal.

## What This Is

A wrapper that wires together:
- **NanoClaw** — Claude SDK-powered agent framework
- **signal-cli** — open-source Signal bridge (no app needed)
- **Claude API** — Anthropic's API for the actual AI
- **GitHub CLI** (optional) — for coding and repo management tasks

Your agent runs on a dedicated machine (Mac Mini, Raspberry Pi, Linux box). You message it from Signal like texting someone who can actually do things.

## What You Need

| Requirement | Notes |
|------------|-------|
| Mac or Linux machine | Dedicated is best — Mac Mini M1 is ideal |
| Python 3.10+ | Usually pre-installed |
| Java 17+ | For signal-cli |
| Homebrew | Mac only — install at brew.sh |
| Anthropic API key | Get one at console.anthropic.com |
| Signal phone number | Must be a real number — use a second number or a VoIP line |

The Signal number is for your **agent**, not you. Your agent has its own Signal account it uses to respond to you.

## Setup (~30 minutes)

### 1. Clone this repo

```bash
git clone https://github.com/RedBeret/claude-signal-agent.git
cd claude-signal-agent
```

### 2. Run the installer

```bash
chmod +x setup.sh
./setup.sh
```

This installs dependencies, sets up the Python environment, and walks you through Signal registration.

### 3. Configure your agent

Copy the templates and fill in your details:

```bash
cp config/nanoclaw.json.template ~/.nanoclaw/nanoclaw.json
cp config/identity/SOUL.md.template ~/.nanoclaw/workspace/SOUL.md
cp config/identity/IDENTITY.md.template ~/.nanoclaw/workspace/IDENTITY.md
cp config/identity/USER.md.template ~/.nanoclaw/workspace/USER.md
```

Edit each file — replace `YOUR_*` placeholders with your actual values.
The comments explain what each field does.

### 4. Add your Anthropic API key

```bash
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > ~/.nanoclaw/.env
chmod 600 ~/.nanoclaw/.env
```

### 5. Start the agent

```bash
./scripts/start.sh
```

Send a message to your agent's Signal number. It should respond.

### 6. Run on startup (optional)

```bash
./scripts/install-launchd.sh   # Mac
./scripts/install-systemd.sh   # Linux
```

## How It Works

```
You (Signal) → signal-cli bridge → NanoClaw → Claude API → Response → Signal
```

Your agent:
- Polls Signal for new messages every 5 seconds
- Sends your message to Claude via the Anthropic API
- Returns the response to you on Signal
- Remembers context within a session
- Can be given tools (web search, GitHub, file operations, etc.)

## Security

- Your API key lives in `~/.nanoclaw/.env` — never committed to this repo
- signal-cli runs locally — Signal messages never go through a third-party server
- Agent only responds to phone numbers you explicitly allowlist
- Pre-commit hook blocks accidental secret commits

## Customization

Edit the identity files to define your agent's personality, values, and limits:

| File | What it controls |
|------|-----------------|
| `IDENTITY.md` | Name, role, persona |
| `SOUL.md` | Values, hard limits, communication style |
| `USER.md` | Your profile — who the agent is working with |

See `docs/CUSTOMIZATION.md` for the full guide.

## Troubleshooting

**Agent not responding?**
```bash
./scripts/health-check.sh
```

**Signal not connecting?**
```bash
signal-cli -a YOUR_AGENT_NUMBER receive
```

**Claude API errors?**
```bash
tail -50 ~/.nanoclaw/logs/nanoclaw.log
```

## License

MIT — use it, fork it, share it freely.
