"""
wake_word.py — Local wake-word listener for Project RAY.

Uses the openwakeword library (fully local, no cloud) to detect the
wake phrase via the built-in ``hey_jarvis`` pre-trained model.

Usage:
    from wake_word import start_listener, stop_listener

    def on_wake():
        print("Wake word detected!")

    start_listener(on_wake)   # starts background thread
    # ... main loop continues ...
    stop_listener()           # clean shutdown
"""

import time
import threading
import numpy as np

# pyrefly: ignore [missing-import]
import sounddevice as sd
# pyrefly: ignore [missing-import]
from openwakeword.model import Model as OWWModel


# ==========================================
# CONFIGURATION
# ==========================================
_SAMPLE_RATE = 16000          # openwakeword expects 16 kHz mono
_CHUNK_SAMPLES = 1280         # 80 ms frames (openwakeword default)
_THRESHOLD = 0.5              # Detection confidence threshold (0–1)
_DEBOUNCE_SECONDS = 2.0       # Ignore re-triggers for 2 s after a hit

# Pre-trained model name shipped with openwakeword.
_MODEL_NAME = "hey_jarvis"


# ==========================================
# INTERNAL STATE
# ==========================================
_stop_event = threading.Event()
_ready_event = threading.Event()
_thread: threading.Thread | None = None


def _listener_loop(callback) -> None:
    """Continuously capture mic audio and run wake-word inference.

    Calls *callback()* (with no arguments) each time the wake phrase is
    detected, then debounces for ``_DEBOUNCE_SECONDS`` to prevent
    rapid re-fires.
    """
    # Load model inside the thread so module import stays fast
    print("[wake_word] Loading wake-word model …")
    oww = OWWModel(wakeword_models=[_MODEL_NAME])
    print(f"[wake_word] Listening for wake word (model: {_MODEL_NAME}) …")

    last_trigger_time = 0.0

    # Find preferred mic (same logic as ray.py — prefer Fifine if present)
    device_id = None
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0 and 'fifine' in dev['name'].lower():
            device_id = i
            print(f"[wake_word] Using mic: {dev['name']}")
            break

    _ready_event.set()  # Signal that model + mic are ready

    try:
        with sd.InputStream(
            device=device_id,
            samplerate=_SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=_CHUNK_SAMPLES,
        ) as stream:
            while not _stop_event.is_set():
                data, _ = stream.read(_CHUNK_SAMPLES)
                audio_frame = data.flatten().astype(np.int16)

                # Run prediction — returns dict like {"hey_jarvis": 0.87}
                scores = oww.predict(audio_frame)
                score = scores.get(_MODEL_NAME, 0.0)

                # Debounce: skip if we triggered recently
                now = time.monotonic()
                if now - last_trigger_time < _DEBOUNCE_SECONDS:
                    continue

                if score >= _THRESHOLD:
                    print(f"[wake_word] Detected! (confidence {score:.2f})")
                    last_trigger_time = now
                    try:
                        callback()
                    except Exception as exc:
                        print(f"[wake_word] Callback error: {exc}")

    except Exception as exc:
        if not _stop_event.is_set():
            print(f"[wake_word] Listener error: {exc}")


# ==========================================
# PUBLIC API
# ==========================================
def start_listener(callback) -> None:
    """Start the wake-word listener in a background daemon thread.

    Parameters
    ----------
    callback : callable
        A no-argument function invoked each time the wake phrase is
        detected.  It runs on the listener thread, so keep it fast
        (e.g., set an event or push to a queue).
    """
    global _thread

    if _thread is not None and _thread.is_alive():
        print("[wake_word] Listener is already running.")
        return

    _stop_event.clear()
    _ready_event.clear()
    _thread = threading.Thread(
        target=_listener_loop,
        args=(callback,),
        daemon=True,
        name="RAY-WakeWord",
    )
    _thread.start()


def wait_until_ready() -> None:
    """Block until the wake-word model and mic are fully initialized."""
    _ready_event.wait()


def stop_listener() -> None:
    """Signal the listener thread to stop and wait for it to exit."""
    global _thread
    _stop_event.set()
    if _thread is not None:
        _thread.join(timeout=5)
        _thread = None
    print("[wake_word] Listener stopped.")

