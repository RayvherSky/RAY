"""
audio_capture.py — Microphone recording for Project RAY.

Handles device discovery and silence-based recording using sounddevice.
Returns raw int16 numpy arrays ready for Whisper transcription.
"""

import numpy as np
# pyrefly: ignore [missing-import]
import sounddevice as sd

from config import (
    SAMPLE_RATE,
    SILENCE_THRESHOLD,
    SILENCE_DURATION,
    MAX_RECORD_SECONDS,
    CHUNK_DURATION,
    MIC_KEYWORD,
)


def find_microphone() -> int | None:
    """Return the device index of the preferred mic, or None for default.

    Scans all audio devices and returns the first input device whose
    name contains ``MIC_KEYWORD`` (case-insensitive).
    """
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0 and MIC_KEYWORD in dev['name'].lower():
            print(f"Using: {dev['name']}")
            return i
    return None


def record_until_silence(device_id: int | None = None) -> np.ndarray | None:
    """Record from *device_id* until silence or timeout.

    Returns
    -------
    numpy.ndarray (int16) or None
        The recorded audio in 16 kHz mono int16 format, or ``None`` if
        nothing was captured.
    """
    samples_per_chunk = int(SAMPLE_RATE * CHUNK_DURATION)
    max_chunks = int(MAX_RECORD_SECONDS / CHUNK_DURATION)

    recording: list[np.ndarray] = []
    silent_chunks = 0

    print("--- Listening... Speak now ---")

    try:
        with sd.InputStream(
            device=device_id,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
        ) as stream:
            for _ in range(max_chunks):
                data, _ = stream.read(samples_per_chunk)
                recording.append(data)

                volume = np.sqrt(np.mean(data ** 2))
                if volume < SILENCE_THRESHOLD:
                    silent_chunks += 1
                else:
                    silent_chunks = 0

                if silent_chunks > SILENCE_DURATION / CHUNK_DURATION:
                    break

        if not recording:
            return None

        audio = np.concatenate(recording)
        # Convert float32 → int16 for Whisper
        audio_int16 = (audio * 32767).astype(np.int16)
        return audio_int16

    except Exception as e:
        print(f"Recording error: {e}")
        return None
