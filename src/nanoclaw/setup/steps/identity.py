"""Step 5: Agent identity customization."""

import importlib.resources
from pathlib import Path

import questionary

from ..ui import step_header, ok, info, console
from ..state import WizardState


PERSONALITIES = {
    "Professional and concise": "Direct, efficient, no filler. Gets to the point. Confident in expertise, honest about limits.",
    "Friendly and warm": "Warm, approachable, conversational. Uses natural language. Celebrates wins, gently flags issues.",
    "Technical and direct": "Terse, precise, technical. Speaks in specifics. Minimal pleasantries, maximum signal.",
}


def _find_template(name: str) -> str:
    """Find a template file, checking repo config/ dir and package resources."""
    # Check relative to this file (repo layout)
    repo_config = Path(__file__).parent.parent.parent.parent.parent / "config" / "identity" / name
    if repo_config.exists():
        return repo_config.read_text()

    # Fallback: generate minimal template
    templates = {
        "SOUL.md.template": (
            "# Soul\n\n"
            "## Hard Limits\n"
            "- Never expose API keys, credentials, or tokens\n"
            "- Never help access systems without authorization\n\n"
            "## Character\n"
            "YOUR_PERSONALITY\n\n"
            "## Dedicated Machine\n"
            "This machine exists solely for YOUR_AGENT_NAME.\n"
            "Act autonomously. Do the work.\n"
        ),
        "IDENTITY.md.template": (
            "# Identity\n\n"
            "**Name:** YOUR_AGENT_NAME\n"
            "**Role:** Personal digital operator\n\n"
            "## User\n"
            "**Name:** YOUR_NAME\n"
            "**Address as:** YOUR_PREFERRED_NAME\n"
        ),
        "USER.md.template": (
            "# User Profile\n\n"
            "| Field | Value |\n|---|---|\n"
            "| **Name** | YOUR_NAME |\n\n"
            "## Background\n"
            "YOUR_BACKGROUND\n\n"
            "## Communication Preferences\n"
            "- Direct, no corporate speak\n"
        ),
    }
    return templates.get(name, "")


def run(state: WizardState):
    step_header(5, "Agent Identity")

    console.print("  Let's give your agent a personality.\n")

    agent_name = questionary.text(
        "Agent name:",
        default="Agent",
    ).ask() or "Agent"

    user_name = questionary.text(
        "Your name:",
    ).ask() or "User"

    preferred_name = questionary.text(
        "How should the agent address you?",
        default=user_name.split()[0],
    ).ask() or user_name

    background = questionary.text(
        "Brief description of yourself (profession, interests):",
    ).ask() or ""

    personality_choice = questionary.select(
        "Agent personality:",
        choices=list(PERSONALITIES.keys()) + ["Custom"],
    ).ask()

    if personality_choice == "Custom":
        personality = questionary.text(
            "Describe the personality in a sentence or two:",
        ).ask() or PERSONALITIES["Professional and concise"]
    else:
        personality = PERSONALITIES[personality_choice]

    state.set("agent_name", agent_name)
    state.set("user_name", user_name)
    state.set("preferred_name", preferred_name)

    # Write identity files
    ws = Path.home() / ".nanoclaw" / "workspace"
    ws.mkdir(parents=True, exist_ok=True)

    # SOUL.md
    soul = _find_template("SOUL.md.template")
    soul = soul.replace("YOUR_AGENT_NAME", agent_name)
    soul = soul.replace("YOUR_NAME", user_name)
    soul = soul.replace("YOUR_PERSONALITY", personality)
    (ws / "SOUL.md").write_text(soul)
    ok("SOUL.md created")

    # IDENTITY.md
    ident = _find_template("IDENTITY.md.template")
    ident = ident.replace("YOUR_AGENT_NAME", agent_name)
    ident = ident.replace("YOUR_NAME", user_name)
    ident = ident.replace("YOUR_PREFERRED_NAME", preferred_name)
    (ws / "IDENTITY.md").write_text(ident)
    ok("IDENTITY.md created")

    # USER.md
    user = _find_template("USER.md.template")
    user = user.replace("YOUR_NAME", user_name)
    user = user.replace("YOUR_BACKGROUND", background or "(not provided)")
    (ws / "USER.md").write_text(user)
    ok("USER.md created")

    # MEMORY.md (if not exists)
    memory_path = ws / "MEMORY.md"
    if not memory_path.exists():
        memory_path.write_text(
            "# Long-Term Memory\n\n"
            "Loaded every session. Keep under 3,000 chars.\n\n"
            "---\n\n"
            "## Deployment Context\n\n"
            f"- **Runtime:** NanoClaw\n"
            f"- **Workspace:** ~/.nanoclaw/workspace/\n\n"
            "## Key Decisions\n\n"
            "## User Preferences\n\n"
            "---\n"
            "*Update incrementally. Daily logs go to memory/YYYY-MM-DD.md*\n"
        )
        ok("MEMORY.md created")
