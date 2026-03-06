"""Setup wizard orchestrator — runs steps in sequence."""

import sys

import questionary

from .ui import banner, console
from .state import WizardState, STEPS
from .steps import (
    welcome,
    dependencies,
    signal_setup,
    api_keys,
    identity,
    agent_config,
    service,
    health,
)

STEP_MODULES = {
    "welcome": welcome,
    "dependencies": dependencies,
    "signal_setup": signal_setup,
    "api_keys": api_keys,
    "identity": identity,
    "agent_config": agent_config,
    "service": service,
    "health": health,
}

STEP_TITLES = {
    "welcome": "Welcome",
    "dependencies": "Dependencies",
    "signal_setup": "Signal Account",
    "api_keys": "API Keys",
    "identity": "Agent Identity",
    "agent_config": "Configuration",
    "service": "System Service",
    "health": "Health Check",
}


def run_wizard():
    """Run the interactive setup wizard."""
    banner()
    state = WizardState()

    # Check for prior run
    if state.has_prior_run:
        next_step = state.next_step
        if next_step:
            idx = STEPS.index(next_step) + 1
            console.print(f"  Previous setup found (completed {len(state.completed)}/{len(STEPS)} steps)")
            choice = questionary.select(
                "What would you like to do?",
                choices=[
                    f"Resume from step {idx} ({STEP_TITLES[next_step]})",
                    "Start fresh",
                    "Exit",
                ],
            ).ask()
            if choice is None or "Exit" in choice:
                return
            if "Start fresh" in choice:
                state.reset()
        else:
            console.print("  [ok]All steps completed previously.[/ok]")
            choice = questionary.select(
                "What would you like to do?",
                choices=["Re-run setup from scratch", "Run health check only", "Exit"],
            ).ask()
            if choice is None or "Exit" in choice:
                return
            if "health check" in choice.lower():
                health.run(state)
                return
            state.reset()

    # Run steps
    for i, step_name in enumerate(STEPS):
        if state.is_done(step_name):
            continue

        module = STEP_MODULES[step_name]
        try:
            module.run(state)
            state.mark_done(step_name)
        except KeyboardInterrupt:
            console.print("\n\n  [warn]Setup interrupted.[/warn] Progress saved — run setup again to resume.")
            state.save()
            sys.exit(0)
        except Exception as e:
            console.print(f"\n  [err]Error in {step_name}: {e}[/err]")
            console.print("  Progress saved — run setup again to resume.")
            state.save()
            sys.exit(1)

    console.print("\n  [bold green]All steps complete.[/bold green]\n")
