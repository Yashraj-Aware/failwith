"""
Terminal output formatter for suggestion blocks.

Renders clean, scannable suggestion output with ANSI colors when supported,
and gracefully degrades to plain text in CI/logs/pipes.
"""

from __future__ import annotations

import os
import sys
import shutil
from typing import Optional

from failwith.suggestions import Suggestion


# ANSI color codes
class _Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"

    # Box drawing
    BOX_TL = "┌"
    BOX_TR = "┐"
    BOX_BL = "└"
    BOX_BR = "┘"
    BOX_H = "─"
    BOX_V = "│"
    ARROW = "→"
    BULB = "💡"
    MAG = "🔍"


class _NoColors:
    """Fallback when colors are not supported."""
    RESET = BOLD = DIM = ""
    YELLOW = CYAN = GREEN = WHITE = GRAY = BLUE = MAGENTA = ""
    BOX_TL = "+"
    BOX_TR = "+"
    BOX_BL = "+"
    BOX_BR = "+"
    BOX_H = "-"
    BOX_V = "|"
    ARROW = "->"
    BULB = "[!]"
    MAG = "[?]"


def _supports_color() -> bool:
    """Detect if the terminal supports ANSI colors."""
    # Explicit override
    if os.environ.get("FAILWITH_NO_COLOR") or os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FAILWITH_FORCE_COLOR"):
        return True

    # Not a TTY (pipe, file, CI)
    if not hasattr(sys.stderr, "isatty") or not sys.stderr.isatty():
        return False

    # Windows needs special handling
    if sys.platform == "win32":
        # Modern Windows Terminal supports ANSI
        return os.environ.get("WT_SESSION") is not None or os.environ.get("TERM_PROGRAM") is not None

    return True


def _get_terminal_width() -> int:
    """Get terminal width, default 80."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def format_suggestion_block(suggestion: Suggestion, config: dict) -> str:
    """
    Format a Suggestion into a terminal-ready string.

    Produces a bordered box with the suggestion title and fixes.
    """
    theme = config.get("theme", "dark")

    if theme == "plain" or not _supports_color():
        return _format_plain(suggestion, config)
    else:
        return _format_colored(suggestion, config)


def _format_colored(suggestion: Suggestion, config: dict) -> str:
    """Format with ANSI colors and box drawing."""
    c = _Colors
    width = min(_get_terminal_width(), 78)
    inner_width = width - 4  # account for "│ " and " │"

    lines = []

    # Top border with title
    header = f" {c.BULB} failwith "
    border_remaining = width - len(" 💡 failwith ") - 2
    top_line = (
        f"{c.GRAY}{c.BOX_TL}{c.BOX_H}"
        f"{c.RESET}{c.BOLD}{c.YELLOW}{header}"
        f"{c.RESET}{c.GRAY}{c.BOX_H * max(border_remaining, 0)}{c.BOX_TR}{c.RESET}"
    )
    lines.append(top_line)

    # Empty line
    lines.append(f"{c.GRAY}{c.BOX_V}{c.RESET}{' ' * (width - 2)}{c.GRAY}{c.BOX_V}{c.RESET}")

    # Title
    title = suggestion.title
    title_line = f"  {c.BOLD}{c.WHITE}{title}{c.RESET}"
    lines.append(
        f"{c.GRAY}{c.BOX_V}{c.RESET}"
        f"{title_line}{' ' * max(0, width - 2 - _visible_len(title) - 2)}"
        f"{c.GRAY}{c.BOX_V}{c.RESET}"
    )

    # Empty line
    lines.append(f"{c.GRAY}{c.BOX_V}{c.RESET}{' ' * (width - 2)}{c.GRAY}{c.BOX_V}{c.RESET}")

    # Fixes
    for fix in suggestion.fixes:
        if fix.startswith("  "):
            # Sub-item (indented)
            colored_fix = f"    {c.DIM}{fix.strip()}{c.RESET}"
        elif fix.startswith(("→", "->")) or ":" in fix[:20]:
            # Command suggestion
            parts = fix.split(":", 1) if ":" in fix[:20] else [fix, ""]
            if len(parts) == 2 and parts[1].strip():
                label = parts[0].strip()
                cmd = parts[1].strip()
                colored_fix = f"  {c.CYAN}{c.ARROW} {label}:{c.RESET}  {c.GREEN}{cmd}{c.RESET}"
            else:
                colored_fix = f"  {c.CYAN}{c.ARROW}{c.RESET} {c.WHITE}{fix}{c.RESET}"
        else:
            colored_fix = f"  {c.CYAN}{c.ARROW}{c.RESET} {c.WHITE}{fix}{c.RESET}"

        lines.append(
            f"{c.GRAY}{c.BOX_V}{c.RESET}"
            f"{colored_fix}"
            f"{c.GRAY}{c.BOX_V}{c.RESET}"
        )

    # Environment info footer
    if suggestion.env_info:
        lines.append(
            f"{c.GRAY}{c.BOX_V}{c.RESET}{' ' * (width - 2)}{c.GRAY}{c.BOX_V}{c.RESET}"
        )
        env_str = " | ".join(suggestion.env_info)
        env_line = f"  {c.MAG} {c.DIM}{env_str}{c.RESET}"
        lines.append(
            f"{c.GRAY}{c.BOX_V}{c.RESET}"
            f"{env_line}"
            f"{c.GRAY}{c.BOX_V}{c.RESET}"
        )

    # Empty line before bottom
    lines.append(f"{c.GRAY}{c.BOX_V}{c.RESET}{' ' * (width - 2)}{c.GRAY}{c.BOX_V}{c.RESET}")

    # Bottom border
    lines.append(f"{c.GRAY}{c.BOX_BL}{c.BOX_H * (width - 2)}{c.BOX_BR}{c.RESET}")

    return "\n".join(lines)


def _format_plain(suggestion: Suggestion, config: dict) -> str:
    """Format as plain text without colors or box drawing."""
    c = _NoColors
    width = min(_get_terminal_width(), 78)

    lines = []

    # Top border
    lines.append(f"{c.BOX_TL}{c.BOX_H} {c.BULB} failwith {c.BOX_H * (width - 16)}{c.BOX_TR}")

    # Empty line
    lines.append(f"{c.BOX_V}{' ' * (width - 2)}{c.BOX_V}")

    # Title
    title = suggestion.title
    padding = max(0, width - 4 - len(title))
    lines.append(f"{c.BOX_V}  {title}{' ' * padding}{c.BOX_V}")

    # Empty line
    lines.append(f"{c.BOX_V}{' ' * (width - 2)}{c.BOX_V}")

    # Fixes
    for fix in suggestion.fixes:
        prefix = f"  {c.ARROW} " if not fix.startswith("  ") else "    "
        text = fix.strip() if fix.startswith("  ") else fix
        line_content = f"{prefix}{text}"
        padding = max(0, width - 2 - len(line_content))
        lines.append(f"{c.BOX_V}{line_content}{' ' * padding}{c.BOX_V}")

    # Environment info
    if suggestion.env_info:
        lines.append(f"{c.BOX_V}{' ' * (width - 2)}{c.BOX_V}")
        env_str = " | ".join(suggestion.env_info)
        env_line = f"  {c.MAG} {env_str}"
        padding = max(0, width - 2 - len(env_line))
        lines.append(f"{c.BOX_V}{env_line}{' ' * padding}{c.BOX_V}")

    # Bottom border
    lines.append(f"{c.BOX_V}{' ' * (width - 2)}{c.BOX_V}")
    lines.append(f"{c.BOX_BL}{c.BOX_H * (width - 2)}{c.BOX_BR}")

    return "\n".join(lines)


def _visible_len(s: str) -> int:
    """Get the visible length of a string, excluding ANSI escape codes."""
    import re
    return len(re.sub(r"\033\[[0-9;]*m", "", s))
