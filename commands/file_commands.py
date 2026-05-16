"""
file_commands.py — Everything Search integration for Project RAY.

Handles file searches via voidtools Everything (es.exe) and natural-
language parsing of file-related commands.
"""

import os
import subprocess

from config import ES_PATH, DIRECT_FILE_OPENING


def everything_search(query: str, max_results: int = 1) -> list[str]:
    """Return list of full paths (used only if DIRECT_FILE_OPENING = True)."""
    if not query.strip():
        return []
    try:
        result = subprocess.run(
            [ES_PATH, "-full-path-and-name", "-limit", str(max_results), query],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0 and result.stdout:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return []
    except Exception as e:
        print(f"RAY: Search error - {e}")
        return []


def open_everything_gui(query: str) -> None:
    """Opens Everything's main window with the search pre-filled."""
    try:
        # Everything.exe accepts -search "query"
        everything_exe = "C:\\Program Files\\Everything\\Everything.exe"
        if not os.path.exists(everything_exe):
            # Fallback: try just "Everything" from PATH
            everything_exe = "Everything"
        os.system(f'start "" "{everything_exe}" -search "{query}"')
        print(f"RAY: Opened Everything searching for '{query}'")
    except Exception as e:
        print(f"RAY: Could not open Everything - {e}")


def handle_file_command(user_input: str) -> tuple[str, str] | None:
    """Parse natural language for file searches.

    Returns
    -------
    tuple (action, query) or None
        action is ``"gui"`` or ``"open_direct"``.
    """
    lower = user_input.lower()

    # Pattern: "search for X" or "find X" -> open Everything GUI
    search_keywords = [
        "search for ",
        "find ",
        "look for ",
        "where is ",
        "file search",
        "search files",
        "search files for",
    ]
    for kw in search_keywords:
        if kw in lower:
            query = user_input[lower.index(kw) + len(kw):].strip()
            if query:
                return ("gui", query)

    # Pattern: "everything X" -> open GUI
    if "everything " in lower:
        query = lower.split("everything ", 1)[1].strip()
        return ("gui", query)

    # Pattern: "open file X" or "open my X"
    if DIRECT_FILE_OPENING and ("open file" in lower or ("open my" in lower and "file" in lower)):
        parts = lower.split("open file", 1) if "open file" in lower else lower.split("open my", 1)
        if len(parts) > 1:
            query = parts[1].strip()
            return ("open_direct", query)

    return None
