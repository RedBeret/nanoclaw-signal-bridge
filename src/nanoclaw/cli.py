"""NanoClaw CLI — AI agent runtime with Signal integration."""

import asyncio
import logging
import os
import sys

os.environ.pop("CLAUDECODE", None)

import click

from .config import Config, NANOCLAW_HOME
from .orchestrator import Orchestrator


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def get_config() -> Config:
    try:
        return Config()
    except FileNotFoundError:
        click.echo(f"Config not found at {NANOCLAW_HOME / 'nanoclaw.json'}", err=True)
        click.echo("Run: nanoclaw setup", err=True)
        sys.exit(1)


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def cli(verbose: bool):
    """NanoClaw — AI agent runtime with Signal integration."""
    setup_logging(verbose)


@cli.command()
@click.argument("agent", default="main")
@click.argument("prompt", nargs=-1, required=True)
@click.option("--resume/--no-resume", default=False, help="Resume previous session")
def run(agent: str, prompt: tuple, resume: bool):
    """Run a one-shot task with an agent."""
    config = get_config()
    orchestrator = Orchestrator(config)
    prompt_text = " ".join(prompt)

    click.echo(f"[{agent}] Processing: {prompt_text[:80]}...")

    async def _run():
        return await orchestrator.run_task(
            agent, prompt_text, resume=resume,
            stream_callback=lambda t: click.echo(t, nl=False),
        )

    try:
        result = asyncio.run(_run())
        click.echo()
        if result:
            click.echo(f"\n--- Result ---\n{result}")
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)


@cli.command()
@click.argument("agent", default="main")
def chat(agent: str):
    """Interactive chat session with an agent."""
    config = get_config()
    orchestrator = Orchestrator(config)

    click.echo(f"NanoClaw chat — agent: {agent} (Ctrl+C to exit)")
    click.echo("---")

    async def _chat():
        while True:
            try:
                prompt = click.prompt("you", prompt_suffix="> ")
            except (EOFError, click.Abort):
                click.echo("\nBye.")
                break

            if prompt.strip().lower() in ("exit", "quit", "bye"):
                click.echo("Bye.")
                break

            await orchestrator.run_task(
                agent, prompt, resume=True,
                stream_callback=lambda t: click.echo(t, nl=False),
            )
            click.echo()

    asyncio.run(_chat())


@cli.command()
def daemon():
    """Run as daemon with Signal channel listener."""
    config = get_config()
    orchestrator = Orchestrator(config)

    if not config.signal_config:
        click.echo("Signal channel not enabled in nanoclaw.json", err=True)
        sys.exit(1)

    from .channels.signal import SignalChannel

    channel = SignalChannel(config, orchestrator)
    click.echo("NanoClaw daemon starting (Signal channel)...")

    async def _daemon():
        try:
            await channel.run()
        except KeyboardInterrupt:
            channel.stop()
            click.echo("\nDaemon stopped.")

    asyncio.run(_daemon())


@cli.command()
def status():
    """Show system status and health check."""
    config = get_config()
    orchestrator = Orchestrator(config)
    health = asyncio.run(orchestrator.health_check())

    click.echo("NanoClaw Status")
    click.echo("===============")
    for key, value in health.items():
        if isinstance(value, list):
            click.echo(f"  {key}: {', '.join(value)}")
        else:
            click.echo(f"  {key}: {value}")


@cli.command()
def agents():
    """List configured agents."""
    config = get_config()
    for name, agent_def in config.agents_list.items():
        model = agent_def.get("model", config.agents_defaults.get("model", "?"))
        desc = agent_def.get("description", "")
        skills = agent_def.get("skills", [])
        click.echo(f"  {name:12s} [{model}] {desc}")
        if skills:
            click.echo(f"               skills: {', '.join(skills)}")


@cli.command("setup")
def setup_cmd():
    """Run the interactive setup wizard."""
    from .setup import setup_main
    setup_main()


if __name__ == "__main__":
    cli()
