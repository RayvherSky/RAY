"""
app_commands.py — Command dispatcher for Project RAY.

Resolves aliases, matches app commands, delegates file commands,
and executes the appropriate action.
"""

import os
import webbrowser

from config import APP_COMMANDS, ALIASES, EXIT_PHRASES
from tts_engine import speak
from commands.file_commands import (
    handle_file_command,
    everything_search,
    open_everything_gui,
)


def execute_command(command_text: str) -> bool:
    """Process *command_text* and execute the matching action.

    Returns
    -------
    bool
        ``True`` to keep running, ``False`` to exit.
    """
    if not command_text:
        speak("I didn't hear anything.")
        return True

    # Normalize
    command_text = command_text.lower().strip().rstrip('.,!?;')

    # Exit commands
    if command_text in EXIT_PHRASES:
        speak("Shutting down. Talk to you later!")
        return False

    # Check for file-related commands first
    file_cmd = handle_file_command(command_text)
    if file_cmd:
        action, query = file_cmd
        if action == "gui":
            open_everything_gui(query)
        elif action == "open_direct":
            results = everything_search(query, max_results=1)
            if results:
                file_path = results[0]
                speak(f"Opening '{file_path}'...")
                os.startfile(file_path)
            else:
                speak(f"No file found for '{query}'.")
                # Fallback to Everything GUI
                open_everything_gui(query)
        return True

    # Resolve aliases
    command = command_text.lower().strip()
    if command in ALIASES:
        command = ALIASES[command]

    # Match app commands
    for cmd_phrase, action in APP_COMMANDS.items():
        if cmd_phrase in command:
            speak(f"Executing '{action}'...")
            try:
                if action.startswith('start https://') or action.startswith('start http://'):
                    url = action.split(' ', 1)[1]
                    webbrowser.open(url)
                else:
                    os.system(action)
                speak("Done.")
            except Exception as e:
                speak(f"Error - {e}")
            return True

    speak(f"I don't know how to do '{command_text}'.")
    return True
