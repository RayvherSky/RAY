"""
tts_engine.py — Non-blocking TTS engine for Project RAY.

Wraps pyttsx3 in a daemon thread so the main loop never blocks on speech.
Exposes the same speak(text) interface as the original ray.py so main.py
needs zero changes.

Usage:
    from tts_engine import speak
    speak("Hello, I am RAY.")  # returns immediately
"""

import threading
import queue
import atexit

# pyrefly: ignore [missing-import]
import pyttsx3

from config import TTS_RATE, TTS_VOICE_INDEX


# ==========================================
# INTERNAL STATE
# ==========================================
_tts_queue: queue.Queue[str | None] = queue.Queue()
_engine_ready = threading.Event()


def _worker() -> None:
    """Background worker that owns the pyttsx3 engine.

    pyttsx3 is NOT thread-safe — all engine calls must happen on the
    same thread that called pyttsx3.init().  This worker thread is the
    sole owner of the engine instance.
    """
    engine = pyttsx3.init()

    # Voice settings pulled from config.py
    engine.setProperty('rate', TTS_RATE)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[TTS_VOICE_INDEX].id)

    _engine_ready.set()  # Signal that the engine is initialized

    while True:
        text = _tts_queue.get()       # blocks until something arrives
        if text is None:              # poison pill → shut down
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as exc:
            print(f"[tts_engine] Error during speech: {exc}")
        finally:
            _tts_queue.task_done()

    # Clean up
    try:
        engine.stop()
    except Exception:
        pass


# ==========================================
# START THE DAEMON THREAD
# ==========================================
_thread = threading.Thread(target=_worker, daemon=True, name="RAY-TTS")
_thread.start()
_engine_ready.wait()  # Block module import until engine is ready


# ==========================================
# PUBLIC API
# ==========================================
def speak(text: str) -> None:
    """Queue *text* for speech and return immediately.

    The text is printed to the console right away (so the user sees it
    before it's spoken) and then pushed to the background TTS worker.
    Drop-in replacement for the old blocking ``speak()`` in ray.py.
    """
    print(f"RAY: {text}")
    _tts_queue.put(text)


def wait_until_done() -> None:
    """Block until every queued utterance has been spoken.

    Useful before exiting so the goodbye message isn't cut short.
    """
    _tts_queue.join()


def shutdown() -> None:
    """Send the poison pill and wait for the worker to exit cleanly."""
    _tts_queue.put(None)
    _thread.join(timeout=5)


# Ensure clean shutdown even if the caller forgets
atexit.register(shutdown)
