"""
ray.py — Main entry point for Project RAY.

Orchestration only — all business logic lives in modules:
  config.py          → user settings
  tts_engine.py      → non-blocking TTS
  wake_word.py       → wake-word listener
  stt_engine.py      → Whisper transcription
  audio_capture.py   → sounddevice recording
  commands/          → command dispatch & file search
"""

import threading
import queue

from tts_engine import speak, wait_until_done
from wake_word import start_listener, stop_listener, wait_until_ready
from stt_engine import listen_for_command
from commands.app_commands import execute_command
from config import VERSION


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

            if user_input.lower() in ["exit", "quit", "sleep"]:
                speak("Shutting down.")
                is_running = False
                break

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

        is_running = execute_command(command_text)

    # --- Clean shutdown ---
    stop_listener()
    wait_until_done()