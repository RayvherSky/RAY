"""
audio_capture.py — Microphone recording for Project RAY.

Handles device discovery and silence-based recording using sounddevice
with WebRTC VAD for robust voice-activity detection.
Returns raw float32 numpy arrays ready for Whisper transcription.
"""

import numpy as np
# pyrefly: ignore [missing-import]
import sounddevice as sd
# pyrefly: ignore [missing-import]
import webrtcvad

from config import (
    SAMPLE_RATE,
    MAX_RECORD_SECONDS,
    CHUNK_DURATION,
    MIC_KEYWORD,
)

# ── VAD tuning constants ──────────────────────────────────────────
VAD_AGGRESSIVENESS = 2          # 0 = least aggressive … 3 = most
SILENT_FRAME_LIMIT = 10         # consecutive silent 30ms frames → stop
MIN_SPEECH_FRAMES = 3           # require this many speech frames before silence counting
VAD_FRAME_MS = 30               # WebRTC VAD frame size in ms
VAD_FRAME_SAMPLES = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)  # 480 @ 16 kHz


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

    Uses WebRTC VAD to distinguish speech from silence.  Recording
    stops after ``SILENT_FRAME_LIMIT`` consecutive silent 30 ms frames
    (~300 ms of confirmed silence), but only once at least
    ``MIN_SPEECH_FRAMES`` speech frames have been detected.

    Returns
    -------
    numpy.ndarray (float32) or None
        The recorded audio in 16 kHz mono float32 format, or ``None``
        if nothing was captured or MIN_SPEECH_FRAMES was never reached.
    """
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

    samples_per_chunk = int(SAMPLE_RATE * CHUNK_DURATION)
    max_chunks = int(MAX_RECORD_SECONDS / CHUNK_DURATION)

    recording: list[np.ndarray] = []
    silent_frames = 0
    speech_frame_count = 0

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
                recording.append(data.copy())

                # Convert float32 → int16 PCM for VAD
                pcm_data = (data * 32768).astype(np.int16).tobytes()

                # Rechunk 100 ms buffer into 30 ms sub-frames
                frame_bytes = VAD_FRAME_SAMPLES * 2  # 2 bytes per int16 sample
                num_full_frames = len(pcm_data) // frame_bytes

                for f in range(num_full_frames):
                    frame = pcm_data[f * frame_bytes : (f + 1) * frame_bytes]
                    is_speech = vad.is_speech(frame, SAMPLE_RATE)

                    if is_speech:
                        speech_frame_count += 1
                        silent_frames = 0
                    elif speech_frame_count >= MIN_SPEECH_FRAMES:
                        # Only count silence after enough speech frames
                        silent_frames += 1

                    if speech_frame_count >= MIN_SPEECH_FRAMES and silent_frames >= SILENT_FRAME_LIMIT:
                        break

                # Break outer loop too
                if speech_frame_count >= MIN_SPEECH_FRAMES and silent_frames >= SILENT_FRAME_LIMIT:
                    break

        if not recording or speech_frame_count < MIN_SPEECH_FRAMES:
            return None

        audio = np.concatenate(recording).flatten()
        return audio  # float32, as expected by the rest of the pipeline

    except Exception as e:
        print(f"Recording error: {e}")
        return None
