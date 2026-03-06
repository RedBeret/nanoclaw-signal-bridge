"""Authentication helpers — short-lived tokens from system keychains."""

import logging
import subprocess

log = logging.getLogger("nanoclaw")


def get_gh_token() -> str | None:
    """Get GitHub token from gh CLI keyring."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        token = result.stdout.strip()
        if result.returncode == 0 and token:
            return token
    except (FileNotFoundError, subprocess.TimeoutExpired):
        log.warning("gh CLI not available — GitHub MCP will be disabled")
    return None
