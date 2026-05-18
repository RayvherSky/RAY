"""
ray.py — Main entry point for Project RAY.

Orchestration only — all business logic lives in modules:
  config.py          → user settings
  tts_engine.py      → non-blocking TTS
  wake_word.py       → wake-word listener
  stt_engine.py      → Whisper transcription
  audio_capture.py   → sounddevice recording
  commands/          → command dispatch, intent parsing & file search
"""

import os
import threading
import queue
import webbrowser

from tts_engine import speak, wait_until_done
from wake_word import start_listener, stop_listener, wait_until_ready
from stt_engine import listen_for_command
from commands.intent_parser import parse_intent
from commands.web_commands import handle_web_search
from commands.file_commands import (
    handle_file_command,
    everything_search,
    open_everything_gui,
)
from config import VERSION, APP_COMMANDS, ALIASES


# ==========================================
# NON-BLOCKING INPUT (background thread)
# ==========================================
_input_queue: queue.Queue[str] = queue.Queue()


def _input_worker():
    """Read stdin in a background thread so the main loop can poll
    both wake-word events and keyboard input without blocking."""
    while True:
        try:
            line = input("> ").strip()
            _input_queue.put(line)
        except EOFError:
            break


# ==========================================
# COMMAND DISPATCH (intent-driven)
# ==========================================
def _dispatch(command_text: str) -> bool:
    """Resolve intent and execute the appropriate action.

    Returns ``True`` to keep running, ``False`` to exit.
    """
    result = parse_intent(command_text)
    print(f"DEBUG intent: source={result['source']}  "
          f"intent={result['intent']}  entity={result['entity']!r}")

    intent = result["intent"]
    entity = result["entity"]

    # ── exit ──────────────────────────────────────────────────────
    if intent == "exit":
        speak("Shutting down. Talk to you later!")
        return False

    # ── open_app ──────────────────────────────────────────────────
    if intent == "open_app":
        # Resolve alias → canonical command if needed
        cmd_key = entity
        if cmd_key in ALIASES:
            cmd_key = ALIASES[cmd_key]

        action = APP_COMMANDS.get(cmd_key)
        if action:
            speak(f"Executing '{action}'...")
            try:
                if action.startswith("start https://") or action.startswith("start http://"):
                    url = action.split(" ", 1)[1]
                    webbrowser.open(url)
                else:
                    os.system(action)
                speak("Done.")
            except Exception as e:
                speak(f"Error - {e}")
        else:
            speak(f"I don't know how to open '{entity}'.")
        return True

    # ── file_search ───────────────────────────────────────────────
    if intent == "file_search":
        if entity:
            # Try direct file open first, fall back to Everything GUI
            file_result = handle_file_command(f"find {entity}")
            if file_result:
                action_type, query = file_result
                if action_type == "gui":
                    open_everything_gui(query)
                elif action_type == "open_direct":
                    results = everything_search(query, max_results=1)
                    if results:
                        file_path = results[0]
                        speak(f"Opening '{file_path}'...")
                        os.startfile(file_path)
                    else:
                        speak(f"No file found for '{query}'.")
                        open_everything_gui(query)
            else:
                open_everything_gui(entity)
        else:
            speak("What file should I search for?")
        return True

    # ── web_search ────────────────────────────────────────────────
    if intent == "web_search":
        if entity:
            response = handle_web_search(entity)
            speak(response)
        else:
            speak("What should I search for?")
        return True

    # ── unknown ───────────────────────────────────────────────────
    speak("I don't know how to do that yet.")
    return True


# ==========================================
# MAIN LOOP (Wake Word + Voice + Text)
# ==========================================
if __name__ == "__main__":
    # --- Wake word setup (start BEFORE the greeting) ---
    wake_event = threading.Event()

    def on_wake():
        """Called by wake_word listener thread when 'hey jarvis' is detected."""
        wake_event.set()

    start_listener(on_wake)
    wait_until_ready()  # Block until wake-word model + mic are loaded

    # All modules ready — now greet
    speak(f"Project RAY version {VERSION} is online and ready.")

    # --- Non-blocking input thread ---
    input_thread = threading.Thread(target=_input_worker, daemon=True, name="RAY-Input")
    input_thread.start()

    is_running = True
    while is_running:
        print("\n[Say the wake word, press ENTER to speak, or type a command]")

        # Poll both sources: wake word event + keyboard input
        command_text = None
        while command_text is None:
            # Check wake word
            if wake_event.is_set():
                wake_event.clear()
                print("[Wake word detected — listening for command...]")
                user_command = listen_for_command()
                if user_command:
                    command_text = user_command
                else:
                    speak("I didn't hear anything after the wake word.")
                    print("\n[Say the wake word, press ENTER to speak, or type a command]")
                continue

            # Check keyboard input (non-blocking)
            try:
                user_input = _input_queue.get(timeout=0.2)
            except queue.Empty:
                continue  # No input yet — loop back and check wake_event

            if user_input == "":
                # Empty ENTER -> manual voice trigger
                user_command = listen_for_command()
                if not user_command:
                    speak("I didn't hear anything.")
                    print("\n[Say the wake word, press ENTER to speak, or type a command]")
                    continue
                command_text = user_command
            else:
                # User typed a text command
                command_text = user_input

        if not is_running:
            break

        # Normalize: lowercase, strip, remove trailing punctuation
        command_text = command_text.lower().strip().rstrip('.,!?;')

        is_running = _dispatch(command_text)

    # --- Clean shutdown ---
    stop_listener()
    wait_until_done()