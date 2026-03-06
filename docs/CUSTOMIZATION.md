# Customizing Your Agent

The three identity files control your agent's personality, values, and how it relates to you.
Edit them after setup to make the agent yours.

## SOUL.md — Values and Limits

This is the agent's core. It loads every session and defines:
- What it will **never** do (hard limits)
- Its general approach and character
- Security rules

Keep it short (under 2,000 chars). The shorter it is, the more room for actual work.

**What to customize:**
- Add any specific limits relevant to your use case
- Adjust the character description to match your preferred working style

## IDENTITY.md — Name and Persona

Defines the agent's name, role, and how it presents itself.

**What to customize:**
- Change the name (default: Alfred, because it's a classic)
- Adjust the persona description
- Set who it works with (your name, how it should address you)

## USER.md — Your Profile

This tells the agent about you so it doesn't have to ask basic questions repeatedly.

**What to fill in:**
- Your background and profession
- What you want to use the agent for
- Your communication preferences
- Your tech stack and tools

**More detail = better answers.** The agent uses this to calibrate response depth,
technical level, and what context to include or skip.

## MEMORY.md — Persistent Memory

The agent reads and writes this file to remember things across sessions.

You can pre-populate it with things you always want the agent to know:
- Standing decisions ("always use PostgreSQL, not MySQL")
- Active projects and their status
- Preferences ("never suggest Redux, I use Zustand")

## Adding Skills

Skills are Markdown files in `~/.nanoclaw/workspace/skills/` that the agent reads
when it needs to perform specialized work. Think of them as instruction modules.

You can write your own or use the ones included in this repo's `workspace/skills/` directory.

**To add a skill:**
1. Create `~/.nanoclaw/workspace/skills/my-skill.md`
2. Write it in plain English — what the agent should know for that domain
3. The agent will reference it when relevant

**Example skill topics:**
- Your specific dev environment and tools
- Your organization's code style and conventions
- Domain knowledge for your field
- Specific workflows you do repeatedly

## Schedules

Edit `nanoclaw.json` to add automated tasks that run on a cron schedule.

Common ones to add:
```json
{
  "name": "morning_briefing",
  "cron": "0 8 * * *",
  "prompt": "Summarize yesterday, list today's priorities, send via Signal."
},
{
  "name": "github_check",
  "cron": "0 9,17 * * *",
  "prompt": "Check for new PRs, failing CI, Dependabot alerts. Report via Signal if actionable."
}
```

See the template `nanoclaw.json` for the full format and more examples.
