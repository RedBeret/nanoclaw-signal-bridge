"""Agent definition loader — reads config + skill files, builds system prompts."""

import logging
import re
from pathlib import Path

import yaml

from .auth import get_gh_token
from .config import Config

log = logging.getLogger("nanoclaw")


def parse_skill_frontmatter(skill_path: Path) -> dict:
    """Parse YAML frontmatter from a SKILL.md file."""
    text = skill_path.read_text()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}
    return {}


def load_skill_content(skill_path: Path) -> str:
    """Load full skill content (without frontmatter)."""
    text = skill_path.read_text()
    match = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
    if match:
        return text[match.end():]
    return text


def build_system_prompt(config: Config, agent_name: str) -> str:
    """Build the full system prompt for an agent by concatenating identity + skills."""
    ws = config.workspace
    parts: list[str] = []

    for fname in ("SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md"):
        fpath = ws / fname
        if fpath.exists():
            parts.append(fpath.read_text().strip())

    agent_def = config.agents_list.get(agent_name, {})
    skill_names = agent_def.get("skills", [])
    skills_dir = ws / "skills"

    for skill_name in skill_names:
        skill_path = skills_dir / skill_name / "SKILL.md"
        if skill_path.exists():
            content = load_skill_content(skill_path)
            if content.strip():
                parts.append(f"## Skill: {skill_name}\n\n{content.strip()}")

    parts.append(_builtin_tool_instructions(config))

    memory_path = ws / "MEMORY.md"
    if memory_path.exists():
        parts.append(memory_path.read_text().strip())

    return "\n\n---\n\n".join(parts)


def _builtin_tool_instructions(config: Config) -> str:
    """Instructions for using Signal, memory, and SSH via Bash."""
    sig = config.signal_config or {}
    account = sig.get("account", "YOUR_AGENT_NUMBER")
    allowlist = sig.get("allowlist", [])
    recipient = allowlist[0] if allowlist else "YOUR_CONTACT_NUMBER"
    if recipient and not recipient.startswith("+"):
        recipient = "+" + recipient

    nodes = config.nodes
    node_lines = ""
    for name, host in nodes.items():
        node_lines += f'\n```bash\nssh {host} "command here"  # {name}\n```'

    signal_section = f"""### Signal Messaging
Send a message:
```bash
curl -s -X POST http://127.0.0.1:19756/api/v1/rpc -H 'Content-Type: application/json' -d \
'{{"jsonrpc":"2.0","method":"send","params":{{"account":"{account}","message":"YOUR MESSAGE",\
"recipient":["{recipient}"]}},"id":1}}'
```
Receive messages:
```bash
signal-cli --output=json -a {account} receive -t 3
```
Only send to allowlisted contacts: {', '.join(allowlist) if allowlist else 'see config allowlist'}."""

    remote_section = ""
    if nodes:
        remote_section = f"""
### Remote Execution (Network Nodes)
{node_lines}
Use for GPU tasks, platform-specific commands, or heavy computation."""

    return f"""## Built-in Tools (use via Bash)

{signal_section}

### Memory System
- Persistent memory: `~/.nanoclaw/workspace/MEMORY.md` (read/edit directly)
- Daily logs: `~/.nanoclaw/workspace/memory/YYYY-MM-DD.md`
- Search memory: `grep -rni "pattern" ~/.nanoclaw/workspace/memory/`
- Append to today's log when completing tasks or learning something important
{remote_section}"""


def get_mcp_servers(config: Config, agent_name: str) -> dict:
    """Build MCP servers dict based on agent skills and config."""
    agent_def = config.agents_list.get(agent_name, {})
    agent_skills = set(agent_def.get("skills", []))
    mcp_config = config.raw.get("mcp_servers", {})
    servers = {}

    for server_name, server_def in mcp_config.items():
        enabled_skills = set(server_def.get("enabled_for_skills", []))
        if not agent_skills & enabled_skills:
            continue

        stype = server_def.get("type", "stdio")

        if stype == "http":
            entry = {"type": "http", "url": server_def["url"]}
            if server_def.get("auth") == "gh_cli":
                token = get_gh_token()
                if token:
                    entry["headers"] = {"Authorization": f"Bearer {token}"}
                else:
                    log.warning("No GitHub token — skipping %s MCP", server_name)
                    continue
            servers[server_name] = entry

        elif stype == "stdio":
            entry = {"command": server_def["command"]}
            if "args" in server_def:
                entry["args"] = server_def["args"]
            if "env" in server_def:
                entry["env"] = server_def["env"]
            servers[server_name] = entry

    if servers:
        log.debug("MCP servers for %s: %s", agent_name, list(servers))
    return servers


def get_agent_options(config: Config, agent_name: str, *, autonomous: bool = False) -> dict:
    """Get SDK options dict for a named agent."""
    defaults = config.agents_defaults
    agent_def = config.agents_list.get(agent_name)
    if not agent_def:
        raise ValueError(f"Unknown agent: {agent_name}. Available: {list(config.agents_list)}")

    model = agent_def.get("model", defaults.get("model", "claude-sonnet-4-6"))
    tools = agent_def.get("tools", ["Read", "Write", "Edit", "Bash", "Glob", "Grep"])

    if autonomous:
        permission_mode = "bypassPermissions"
    else:
        permission_mode = defaults.get("permission_mode", "acceptEdits")

    mcp_servers = get_mcp_servers(config, agent_name)

    for server_name in mcp_servers:
        tools.append(f"mcp__{server_name}__*")

    return {
        "model": model,
        "system_prompt": build_system_prompt(config, agent_name),
        "allowed_tools": tools,
        "permission_mode": permission_mode,
        "max_turns": defaults.get("max_turns", 50),
        "cwd": str(config.workspace),
        "mcp_servers": mcp_servers,
    }
