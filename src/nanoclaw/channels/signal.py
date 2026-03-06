"""Signal channel — listens for incoming messages and routes to agents.

Supports two modes:
1. JSON-RPC mode: Uses signal-cli daemon HTTP API (when daemon is running)
2. Direct CLI mode: Spawns signal-cli processes (when no daemon)
"""

import asyncio
import json
import logging
import re
import subprocess
from urllib.request import Request, urlopen
from urllib.error import URLError

from ..config import Config
from ..orchestrator import Orchestrator
from ..stores.conversations import add_message, get_context_window

log = logging.getLogger("nanoclaw.signal")

SIGNAL_RPC_URL = "http://127.0.0.1:19756/api/v1/rpc"


def _rpc_call(method: str, params: dict, timeout: int = 30) -> dict | None:
    """Make a JSON-RPC call to signal-cli daemon."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }).encode()
    req = Request(SIGNAL_RPC_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (URLError, TimeoutError, json.JSONDecodeError) as e:
        log.debug("RPC call failed: %s", e)
        return None


def _daemon_running() -> bool:
    try:
        result = _rpc_call("version", {}, timeout=3)
        return result is not None and "error" not in result
    except Exception:
        return False


class SignalChannel:
    """Polls signal-cli for messages and routes them through the orchestrator."""

    def __init__(self, config: Config, orchestrator: Orchestrator):
        self.config = config
        self.orchestrator = orchestrator
        self._running = False
        self._daemon_proc = None

        sig = config.signal_config
        if not sig:
            raise ValueError("Signal channel not enabled in config")
        self.account = sig["account"]
        self.allowlist = set(sig.get("allowlist", []))
        self.poll_interval = sig.get("poll_interval_seconds", 5)

    def _normalize_number(self, number: str) -> str:
        return number.lstrip("+")

    def _is_allowed(self, sender: str) -> bool:
        normalized = self._normalize_number(sender)
        return any(self._normalize_number(a) == normalized for a in self.allowlist)

    def _start_daemon(self):
        if _daemon_running():
            log.info("Signal daemon already running on port 19756")
            return

        log.info("Starting signal-cli daemon on port 19756...")
        self._daemon_proc = subprocess.Popen(
            [
                "signal-cli", "-a", self.account,
                "daemon", "--http", "127.0.0.1:19756",
                "--receive-mode=manual",
                "--send-read-receipts",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        import time
        for _ in range(20):
            time.sleep(0.5)
            if _daemon_running():
                log.info("Signal daemon started (PID %d)", self._daemon_proc.pid)
                return
        log.error("Signal daemon failed to start within 10s")

    def _receive_messages_rpc(self) -> list[dict]:
        result = _rpc_call("receive", {"timeout": 5}, timeout=15)
        if not result or "result" not in result:
            return []

        messages = []
        for item in result.get("result", []):
            envelope = item.get("envelope", {})
            data = envelope.get("dataMessage", {})
            text = data.get("message", "")
            sender = envelope.get("source", "") or envelope.get("sourceNumber", "")
            if text and sender:
                messages.append({"sender": sender, "text": text})
        return messages

    def _receive_messages_cli(self) -> list[dict]:
        try:
            result = subprocess.run(
                [
                    "signal-cli", "--output=json",
                    "-a", self.account,
                    "receive", "-t", "3",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            log.debug("signal-cli receive: %s", e)
            return []

        messages = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                msg = json.loads(line)
                envelope = msg.get("envelope", {})
                data = envelope.get("dataMessage", {})
                text = data.get("message", "")
                sender = envelope.get("source", "")
                if text and sender:
                    messages.append({"sender": sender, "text": text})
            except json.JSONDecodeError:
                continue
        return messages

    def _send_reply_rpc(self, recipient: str, text: str) -> bool:
        result = _rpc_call("send", {
            "account": self.account,
            "message": text,
            "recipient": [recipient],
        })
        if result and "result" in result:
            log.info("Reply sent to %s (%d chars) via RPC", recipient, len(text))
            return True
        log.warning("RPC send failed: %s", result)
        return False

    def _send_reply_cli(self, recipient: str, text: str):
        try:
            subprocess.run(
                ["signal-cli", "-a", self.account, "send", "-m", text, recipient],
                capture_output=True,
                text=True,
                timeout=60,
            )
            log.info("Reply sent to %s (%d chars) via CLI", recipient, len(text))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            log.error("Failed to send Signal reply to %s", recipient)

    def _send_reply(self, recipient: str, text: str):
        if not self._send_reply_rpc(recipient, text):
            self._send_reply_cli(recipient, text)

    async def run(self):
        """Main loop — start daemon, poll for messages, process with agent, reply."""
        self._running = True

        subprocess.run(["pkill", "-f", "signal-cli.*daemon"], capture_output=True)
        await asyncio.sleep(2)

        self._start_daemon()
        log.info("Signal channel started (account=%s, polling every %ds)", self.account, self.poll_interval)

        while self._running:
            try:
                messages = self._receive_messages_rpc()
            except Exception as e:
                log.error("Error receiving messages: %s", e)
                await asyncio.sleep(self.poll_interval)
                continue

            for msg in messages:
                sender = msg["sender"]
                text = msg["text"]

                if not self._is_allowed(sender):
                    log.warning("Blocked message from non-allowlisted sender: %s", sender)
                    continue

                log.info("Message from %s: %s", sender, text[:80])
                add_message(sender, "in", text)

                history = get_context_window(sender, max_chars=4000)
                if history and history.strip() != f"You: {text}":
                    prompt = f"[Conversation history]\n{history}\n\n[New message]\n{text}"
                else:
                    prompt = text

                try:
                    result = await self.orchestrator.run_task("main", prompt, autonomous=True)
                    if len(result) > 4000:
                        result = result[:3950] + "\n\n[truncated]"
                    self._send_reply(sender, result)
                    add_message(sender, "out", result)
                except Exception as e:
                    log.exception("Error processing message from %s", sender)
                    error_msg = f"Sorry, hit an error: {e}"
                    self._send_reply(sender, error_msg)
                    add_message(sender, "out", error_msg)

            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False
        if self._daemon_proc:
            self._daemon_proc.terminate()
            log.info("Signal daemon stopped")
