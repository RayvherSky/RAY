"""
web_commands.py — Web search handler for Project RAY.

Opens DuckDuckGo searches in the default browser.
"""

import webbrowser


def handle_web_search(query: str) -> str:
    """Open a DuckDuckGo search in the default browser.

    Returns a confirmation string suitable for TTS.
    """
    webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
    return f"Searching for {query}"
