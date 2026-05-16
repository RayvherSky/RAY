import os
import webbrowser
import subprocess
# pyrefly: ignore [missing-import]
import pyttsx3
# pyrefly: ignore [missing-import]
import speech_recognition as sr
# pyrefly: ignore [missing-import]
from faster_whisper import WhisperModel
import tempfile
# pyrefly: ignore [missing-import]
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav

# ==========================================
# VOICE ENGINE (TTS)
# ==========================================
engine = pyttsx3.init()

# Optional: Tweak the voice settings (speed and which voice to use)
engine.setProperty('rate', 170) # 170 is a good, natural talking speed
voices = engine.getProperty('voices')
# Usually voices[0] is male, voices[1] is female. Change the index to test them!
engine.setProperty('voice', voices[0].id) 

def speak(text):
    """Makes RAY speak the text out loud."""
    print(f"RAY: {text}")
    engine.say(text)
    engine.runAndWait()

# ==========================================
# LISTENING ENGINE (STT)
# ==========================================
print("RAY: Loading local AI audio model (this takes a few seconds)...")
# 'base.en' is lightweight and English-only, making it incredibly fast.
whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
recognizer = sr.Recognizer()

def listen_for_command():
    # Find mic by name
    device_id = None
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0 and 'fifine' in dev['name'].lower():
            device_id = i
            print(f"Using: {dev['name']}")
            break
    
    samplerate = 16000
    print("--- Listening... Speak now ---")
    
    # Record in chunks until silence
    recording = []
    silence_threshold = 0.01  # adjust if needed
    silence_duration = 1.0    # seconds of silence to stop
    chunk_duration = 0.1      # 100ms chunks
    samples_per_chunk = int(samplerate * chunk_duration)
    
    silent_chunks = 0
    max_chunks = int(5 / chunk_duration)  # 5 second max
    
    try:
        with sd.InputStream(device=device_id, samplerate=samplerate, channels=1, dtype='float32') as stream:
            for _ in range(max_chunks):
                data, _ = stream.read(samples_per_chunk)
                recording.append(data)
                # Check volume
                volume = np.sqrt(np.mean(data**2))
                if volume < silence_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                if silent_chunks > silence_duration / chunk_duration:
                    break
        
        if not recording:
            return ""
        
        audio = np.concatenate(recording)
        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav.write(f.name, samplerate, audio_int16)
            temp_path = f.name
        
        segments, info = whisper_model.transcribe(temp_path, beam_size=5)
        command_text = "".join([segment.text for segment in segments]).strip()
        os.remove(temp_path)
        print(f"DEBUG: Raw recognized text: '{command_text}'")
        print(f"Sky said: '{command_text}'")
        return command_text
        
    except Exception as e:
        print(f"Recording error: {e}")
        return ""


# ==========================================
# CONFIGURATION
# ==========================================

# Path to ES.exe (Everything command line tool)
# Download from: https://www.voidtools.com/downloads/
# Place it somewhere in your PATH, or specify full path:
ES_PATH = "es.exe"  # e.g., "C:\\Tools\\es.exe"

# If True, "open file X" will open the first matching file directly.
# If False, it will open Everything GUI with that search.
DIRECT_FILE_OPENING = True   # Set to False if you prefer Everything GUI only

# App commands (same as before)
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
    "open stremio": 'start stremio',
}

# Custom aliases (nicknames)
ALIASES = {
    "my code thing": "open vs code",
    "the inbox": "open gmail",
    "play music": "open spotify",
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
    "movie time":"open stremio"
}

# ==========================================
# EVERYTHING FUNCTIONS
# ==========================================

def everything_search(query, max_results=1):
    """Return list of full paths (used only if DIRECT_FILE_OPENING = True)."""
    if not query.strip():
        return []
    try:
        result = subprocess.run(
            [ES_PATH, "-full-path-and-name", "-limit", str(max_results), query],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0 and result.stdout:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return []
    except Exception as e:
        print(f"RAY: Search error - {e}")
        return []

def open_everything_gui(query):
    """Opens Everything's main window with the search pre-filled."""
    try:
        # Everything.exe accepts -search "query"
        everything_exe = "C:\\Program Files\\Everything\\Everything.exe"
        if not os.path.exists(everything_exe):
            # Fallback: try just "Everything" from PATH
            everything_exe = "Everything"
        os.system(f'start "" "{everything_exe}" -search "{query}"')
        print(f"RAY: Opened Everything searching for '{query}'")
    except Exception as e:
        print(f"RAY: Could not open Everything - {e}")

def handle_file_command(user_input):
    """Parse natural language for file searches."""
    lower = user_input.lower()
    
    # Pattern: "search for X" or "find X" -> open Everything GUI
    search_keywords = [
        "search for ", 
        "find ", 
        "look for ", 
        "where is ", 
        "file search"
        , "search files", 
        "search files for"]
    for kw in search_keywords:
        if kw in lower:
            query = user_input[lower.index(kw) + len(kw):].strip()
            if query:
                return ("gui", query)   # Open Everything window
    
    # Pattern: "everything X" -> open GUI
    if "everything " in lower:
        query = lower.split("everything ", 1)[1].strip()
        return ("gui", query)
    
    # Pattern: "open file X" or "open my X"
    if DIRECT_FILE_OPENING and ("open file" in lower or ("open my" in lower and "file" in lower)):
        parts = lower.split("open file", 1) if "open file" in lower else lower.split("open my", 1)
        if len(parts) > 1:
            query = parts[1].strip()
            return ("open_direct", query)
    
    return None

# ==========================================
# COMMAND EXECUTION
# ==========================================

def execute_command(command_text):
    if not command_text:
        speak("I didn't hear anything.")
        return True
    
    # Normalize
    command_text = command_text.lower().strip().rstrip('.,!?;')
    
    # Exit commands (now works with "exit" from voice or text)
    if command_text in ["exit", "sleep", "quit"]:
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
                # Optionally open Everything GUI as fallback
                open_everything_gui(query)
        return True
    
    # Resolve aliases and app commands
    command = command_text.lower().strip()
    if command in ALIASES:
        command = ALIASES[command]
    
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

# ==========================================
# MAIN LOOP (Voice + Text)
# ==========================================
if __name__ == "__main__":
    speak("Project RAY version 3 is online and ready.")
    
    is_running = True
    while is_running:
        print("\n[Press ENTER to speak, or type a command and press ENTER]")
        user_input = input("> ").strip()
        
        if user_input.lower() in ["exit", "quit", "sleep"]:
            speak("Shutting down.")
            break
        
        if user_input == "":
            # Empty input -> listen for voice
            user_command = listen_for_command()
            if not user_command:
                speak("I didn't hear anything.")
                continue
            command_text = user_command
        else:
            # User typed something
            command_text = user_input
        
        # Normalize: lowercase, strip, remove trailing punctuation
        command_text = command_text.lower().strip().rstrip('.,!?;')
        
        is_running = execute_command(command_text)