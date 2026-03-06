"""Orchestrator — wraps the LLM SDK for session management and task execution."""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from claude_code_sdk import (
    ClaudeCodeOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    query,
)
from claude_code_sdk._errors import MessageParseError
from claude_code_sdk._internal import message_parser

from .config import Config
from .agents import get_agent_options
from .stores.usage import log_task

log = logging.getLogger("nanoclaw")

# Monkey-patch the SDK message parser to skip unknown message types
# instead of crashing (fixes rate_limit_event, etc.)
_original_parse = message_parser.parse_message


def _safe_parse_message(data):
    try:
        return _original_parse(data)
    except MessageParseError as e:
        if "Unknown message type" in str(e):
            log.debug("Skipping unknown message type: %s", data.get("type", "?"))
            return None
        raise


message_parser.parse_message = _safe_parse_message

try:
    from claude_code_sdk._internal import client as _client_mod
    _client_mod.parse_message = _safe_parse_message
except (ImportError, AttributeError):
    pass


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in ("rate limit", "rate_limit", "too many requests", "429", "try again"))


def _extract_retry_time(exc: Exception) -> str | None:
    msg = str(exc)
    match = re.search(
        r'(?:try again|retry|available|resets?)(?:\s+(?:at|after|in))?\s+'
        r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?|\d+\s*(?:min|hour|sec))', msg
    )
    if match:
        return match.group(1)
    match = re.search(r'(\d+)\s*(?:second|sec|s)\b', msg)
    if match:
        return f"{match.group(1)} seconds"
    match = re.search(r'(\d+)\s*(?:minute|min|m)\b', msg)
    if match:
        return f"{match.group(1)} minutes"
    return None


class Orchestrator:
    """Manages agent sessions, routes tasks, handles rate limits."""

    def __init__(self, config: Config):
        self.config = config
        self._sessions: dict[str, str] = {}
        self._rate_limited = False
        self._rate_limit_until: str | None = None
        self._load_sessions()

    def _sessions_file(self) -> Path:
        return self.config.home / "agents" / "sessions.json"

    def _load_sessions(self):
        sf = self._sessions_file()
        if sf.exists():
            try:
                self._sessions = json.loads(sf.read_text())
            except (json.JSONDecodeError, OSError):
                self._sessions = {}

    def _save_sessions(self):
        sf = self._sessions_file()
        sf.parent.mkdir(parents=True, exist_ok=True)
        sf.write_text(json.dumps(self._sessions, indent=2))

    def _notify_signal(self, message: str):
        """Send a Signal notification to the configured contact."""
        sig = self.config.signal_config
        if not sig:
            return
        account = sig.get("account", "")
        allowlist = sig.get("allowlist", [])
        if not account or not allowlist:
            return
        recipient = allowlist[0]
        if not recipient.startswith("+"):
            recipient = "+" + recipient
        try:
            payload = json.dumps({
                "jsonrpc": "2.0",
                "method": "send",
                "params": {
                    "account": account,
                    "message": message,
                    "recipient": [recipient],
                },
                "id": 1,
            }).encode()
            req = Request(
                "http://127.0.0.1:19756/api/v1/rpc",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=10) as resp:
                resp.read()
        except Exception as e:
            log.debug("Signal notification failed: %s", e)

    async def run_task(
        self,
        agent_name: str,
        prompt: str,
        *,
        resume: bool = False,
        autonomous: bool = False,
        stream_callback=None,
    ) -> str:
        """Run a single task with the named agent. Returns the result text."""
        opts = get_agent_options(self.config, agent_name, autonomous=autonomous)

        sdk_kwargs = {
            "model": opts["model"],
            "system_prompt": opts["system_prompt"],
            "allowed_tools": opts["allowed_tools"],
            "permission_mode": opts["permission_mode"],
            "max_turns": opts["max_turns"],
            "cwd": opts["cwd"],
        }
        if opts.get("mcp_servers"):
            sdk_kwargs["mcp_servers"] = opts["mcp_servers"]
        sdk_opts = ClaudeCodeOptions(**sdk_kwargs)

        if resume and agent_name in self._sessions:
            sdk_opts.resume = self._sessions[agent_name]

        _start = time.monotonic()
        result_text = ""

        try:
            async for message in query(prompt=prompt, options=sdk_opts):
                if message is None:
                    continue
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            if stream_callback:
                                stream_callback(block.text)
                            result_text += block.text
                elif isinstance(message, ResultMessage):
                    if hasattr(message, "result") and message.result:
                        result_text = message.result
                    if hasattr(message, "session_id") and message.session_id:
                        self._sessions[agent_name] = message.session_id
                        self._save_sessions()
        except Exception as e:
            if _is_rate_limit_error(e):
                duration_ms = int((time.monotonic() - _start) * 1000)
                log_task(agent_name, prompt, opts["model"], duration_ms, "rate_limited")
                retry_time = _extract_retry_time(e)
                self._rate_limited = True
                self._rate_limit_until = retry_time
                log.warning("Rate limited! Retry: %s", retry_time or "unknown")
                self._notify_signal(
                    f"[Agent] API rate limit hit. "
                    f"{'Available again: ' + retry_time if retry_time else 'Check back later'}."
                )
                msg = (
                    f"API is rate limited"
                    f"{' until ' + retry_time if retry_time else ''}. "
                    f"Please try again later."
                )
                if stream_callback:
                    stream_callback(msg)
                return msg
            if not result_text:
                duration_ms = int((time.monotonic() - _start) * 1000)
                log_task(agent_name, prompt, opts["model"], duration_ms, "error", error=str(e))
                raise
            log.debug("SDK stream ended with: %s", e)

        self._rate_limited = False
        duration_ms = int((time.monotonic() - _start) * 1000)
        log_task(agent_name, prompt, opts["model"], duration_ms, "success")
        self._append_daily_memory(agent_name, prompt, result_text)

        return result_text

    def _append_daily_memory(self, agent_name: str, prompt: str, result: str):
        today = datetime.now().strftime("%Y-%m-%d")
        memory_dir = self.config.workspace / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        memory_file = memory_dir / f"{today}.md"

        timestamp = datetime.now().strftime("%H:%M")
        summary = result[:200] + "..." if len(result) > 200 else result
        entry = f"\n### {timestamp} [{agent_name}]\n**Prompt:** {prompt[:100]}\n**Result:** {summary}\n"

        if not memory_file.exists():
            header = f"# Session Memory — {today}\n\n---\n"
            memory_file.write_text(header + entry)
        else:
            with open(memory_file, "a") as f:
                f.write(entry)

    async def health_check(self) -> dict:
        return {
            "config": "ok",
            "workspace": str(self.config.workspace),
            "agents": list(self.config.agents_list.keys()),
            "auth": self.config.auth_mode,
            "signal": "enabled" if self.config.signal_config else "disabled",
            "rate_limited": self._rate_limited,
        }
