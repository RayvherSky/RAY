"""
stt_engine.py — Speech-to-text engine for Project RAY.

Loads a local Whisper model and transcribes audio captured via
audio_capture.  Provides the same ``listen_for_command()`` interface
that ray.py uses.
"""

import os
import tempfile

import numpy as np
import scipy.io.wavfile as wav
# pyrefly: ignore [missing-import]
from faster_whisper import WhisperModel

from config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_BEAM_SIZE,
    SAMPLE_RATE,
)
from audio_capture import find_microphone, record_until_silence


# ==========================================
# MODEL LOADING
# ==========================================
print("RAY: Loading local AI audio model (this takes a few seconds)...")
whisper_model = WhisperModel(
    WHISPER_MODEL,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE,
)


def transcribe(audio_int16: np.ndarray) -> str:
    """Transcribe an int16 numpy array and return the text.

    Writes the audio to a temporary WAV file (Whisper needs a file
    path), transcribes it, then deletes the temp file.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, SAMPLE_RATE, audio_int16)
        temp_path = f.name

    try:
        segments, _info = whisper_model.transcribe(
            temp_path, beam_size=WHISPER_BEAM_SIZE
        )
        text = "".join(seg.text for seg in segments).strip()
    finally:
        os.remove(temp_path)

    print(f"DEBUG: Raw recognized text: '{text}'")
    return text


def listen_for_command() -> str:
    """Record from the mic and return the transcribed text.

    Combines ``audio_capture.record_until_silence()`` with Whisper
    transcription.  Returns an empty string if nothing was captured.
    """
    device_id = find_microphone()
    audio = record_until_silence(device_id)

    if audio is None or len(audio) == 0:
        return ""

    text = transcribe(audio)
    if text:
        print(f"Sky said: '{text}'")
    return text
