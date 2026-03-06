"""Conversation store — SQLite-backed message history per sender.

Message content is encrypted at rest using Fernet (AES-128-CBC).
"""

import sqlite3
from pathlib import Path

from .crypto import encrypt, decrypt

DB_PATH = Path.home() / ".nanoclaw" / "conversations.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            sender TEXT NOT NULL,
            direction TEXT NOT NULL,
            content TEXT NOT NULL,
            agent TEXT DEFAULT 'main',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sender_ts
        ON messages(sender, timestamp DESC)
    """)
    conn.commit()
    return conn


def add_message(sender: str, direction: str, content: str, agent: str = "main"):
    """Log a message. direction is 'in' or 'out'. Content is encrypted."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO messages (sender, direction, content, agent) VALUES (?, ?, ?, ?)",
            (sender, direction, encrypt(content), agent),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent(sender: str, limit: int = 10) -> list[dict]:
    """Get last N messages for a sender, oldest first. Content is decrypted."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT direction, content, agent, timestamp FROM messages "
            "WHERE sender = ? ORDER BY id DESC LIMIT ?",
            (sender, limit),
        ).fetchall()
        result = []
        for r in reversed(rows):
            d = dict(r)
            d["content"] = decrypt(d["content"])
            result.append(d)
        return result
    finally:
        conn.close()


def get_context_window(sender: str, max_chars: int = 4000) -> str:
    """Build a conversation context string that fits in max_chars."""
    messages = get_recent(sender, limit=20)
    lines = []
    total = 0
    for msg in messages:
        prefix = "You" if msg["direction"] == "in" else "Agent"
        line = f"{prefix}: {msg['content']}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line) + 1
    return "\n".join(lines)
