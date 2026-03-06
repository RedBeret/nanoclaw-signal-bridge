"""Shared UI helpers for the setup wizard."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

theme = Theme({
    "ok": "green",
    "warn": "yellow",
    "err": "red bold",
    "info": "cyan",
    "step": "bold blue",
    "dim": "dim",
})

console = Console(theme=theme)


def banner():
    console.print()
    console.print(Panel.fit(
        "[bold]NanoClaw Signal Agent[/bold]  v0.2.0\n"
        "Your AI agent, controlled via Signal messenger",
        border_style="blue",
    ))
    console.print()


def step_header(number: int, title: str, total: int = 8):
    console.print()
    console.rule(f"[step]Step {number}/{total} — {title}[/step]")
    console.print()


def ok(msg: str):
    console.print(f"  [ok]✓[/ok] {msg}")


def warn(msg: str):
    console.print(f"  [warn]![/warn] {msg}")


def err(msg: str):
    console.print(f"  [err]✗[/err] {msg}")


def info(msg: str):
    console.print(f"  [info]→[/info] {msg}")


def status_table(rows: list[tuple[str, str, str]]):
    """Display a status table. rows = [(name, status_text, style)]"""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Action")

    for name, status, action in rows:
        if "ok" in status.lower() or "found" in status.lower():
            style = "green"
        elif "not found" in status.lower() or "missing" in status.lower():
            style = "yellow"
        elif "error" in status.lower():
            style = "red"
        else:
            style = ""
        table.add_row(name, f"[{style}]{status}[/{style}]", action)

    console.print(table)


def done_panel(lines: list[str]):
    console.print()
    console.print(Panel(
        "\n".join(lines),
        title="[bold green]Setup Complete[/bold green]",
        border_style="green",
    ))
    console.print()
