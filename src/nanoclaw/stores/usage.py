"""Usage tracker — SQLite-backed task logging and summaries."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .crypto import encrypt


DB_PATH = Path.home() / ".nanoclaw" / "usage.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            agent TEXT NOT NULL,
            prompt_preview TEXT,
            model TEXT,
            started_at DATETIME,
            ended_at DATETIME,
            duration_ms INTEGER,
            status TEXT,
            fallback_used TEXT,
            error TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_ts ON tasks(agent, started_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
    conn.commit()
    return conn


def log_task(
    agent: str,
    prompt: str,
    model: str,
    duration_ms: int,
    status: str,
    fallback_used: str | None = None,
    error: str | None = None,
):
    """Log a completed task."""
    now = datetime.now().isoformat()
    started = (datetime.now() - timedelta(milliseconds=duration_ms)).isoformat()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO tasks (agent, prompt_preview, model, started_at, ended_at, "
            "duration_ms, status, fallback_used, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (agent, encrypt(prompt[:200]), model, started, now, duration_ms, status,
             fallback_used, encrypt(error) if error else None),
        )
        conn.commit()
    finally:
        conn.close()
