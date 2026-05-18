"""
config.py — Central configuration for Project RAY.

All user-configurable values live here so they can be tuned in one
place without touching any logic modules.
"""

VERSION = "0.5"

# ==========================================
# VOICE / TTS SETTINGS
# ==========================================
TTS_RATE = 170              # Words-per-minute for pyttsx3
TTS_VOICE_INDEX = 0         # 0 = male, 1 = female (system dependent)

# ==========================================
# SPEECH-TO-TEXT (Whisper) SETTINGS
# ==========================================
WHISPER_MODEL = "base.en"           # Lightweight, English-only
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_BEAM_SIZE = 5

# ==========================================
# AUDIO CAPTURE SETTINGS
# ==========================================
SAMPLE_RATE = 16000                 # Hz — Whisper expects 16 kHz
SILENCE_THRESHOLD = 0.01            # RMS below this = silence
SILENCE_DURATION = 1.0              # Seconds of silence before auto-stop
MAX_RECORD_SECONDS = 5              # Hard cap on recording length
CHUNK_DURATION = 0.1                # 100 ms per chunk
MIC_KEYWORD = "fifine"              # Preferred mic substring match

# ==========================================
# EVERYTHING SEARCH SETTINGS
# ==========================================

# Path to ES.exe (Everything command line tool)
# Download from: https://www.voidtools.com/downloads/
# Place it somewhere in your PATH, or specify full path:
ES_PATH = "es.exe"  # e.g., "C:\\Tools\\es.exe"

# If True, "open file X" will open the first matching file directly.
# If False, it will open Everything GUI with that search.
DIRECT_FILE_OPENING = True

# ==========================================
# APP COMMANDS
# ==========================================
APP_COMMANDS = {
    "open chrome": 'start chrome --profile-directory="Default"',
    "open gmail": 'start https://mail.google.com',
    "open outlook": 'start https://outlook.live.com',
    "open calendar": 'start outlookcal:',
    "open this pc": 'explorer shell:MyComputerFolder',
    "open file explorer": 'explorer shell:MyComputerFolder',
    "open teams": 'start teams',
    "open discord": 'start discord',
    "open messenger": 'start https://www.messenger.com',
    "open facebook": 'start https://www.facebook.com',
    "open youtube": 'start https://www.youtube.com',
    "open instagram": 'start https://www.instagram.com',
    "open vs code": 'code',
    "open command prompt": 'start cmd',
    "open powershell": 'start powershell',
    "open antigravity": 'start antigravity',
    "open calculator": 'calc',
    "open obsidian": 'start obsidian',
    "open notepad": 'notepad',
    "open task manager": 'taskmgr',
    "open spotify": 'start spotify:',
    "open stremio": '"C:\\Users\\R - Sky Y-Kim\\AppData\\Local\\Programs\\Stremio\\stremio-shell-ng.exe"',
}

# ==========================================
# ALIASES (nicknames → canonical commands)
# ==========================================
ALIASES = {
    "my code thing": "open vs code",
    "the inbox": "open gmail",
    "play music": "open spotify",
    "play some music": "open spotify",
    "calculator": "open calculator",
    "terminal": "open command prompt",
    "cmd": "open command prompt",
    "ps": "open powershell",
    "files": "open file explorer",
    "my computer": "open this pc",
    "launch chrome": "open chrome",
    "start chrome": "open chrome",
    "google chrome": "open chrome",
    "open antigrav": "open antigravity",
    "movie time": "open stremio",
}

# ==========================================
# EXIT PHRASES
# ==========================================
EXIT_PHRASES = [
    "exit", "sleep", "quit", "goodnight", "goodbye",
    "see ya", "good bye", "good night", "see you", "bye",
    "shutdown", "turn off",
]
