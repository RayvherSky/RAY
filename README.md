RAY – Local AI Voice Assistant for Windows
RAY is a local, privacy‑focused AI assistant that can open applications, search your files (via Everything), and be controlled entirely by voice – all on your own machine. No cloud, no API keys, no subscriptions.

✨ Features
Voice control – Push‑to‑talk listening using faster-whisper (local transcription)

Open apps – Launch Chrome, VS Code, Spotify, Teams, Discord, and many more

File search – Integrated with Everything (if installed):

"search for quarterly report" → opens Everything window with results

"open file invoice.pdf" → directly opens the first matching file

Custom aliases – Teach RAY your own phrases ("my code thing" → VS Code)

Text fallback – Type commands when you don’t want to speak

Text‑to‑speech – RAY speaks back using pyttsx3

🖥️ Requirements
Windows (the commands use start, explorer, etc.)

Python 3.10+

Optional but recommended:
Everything (for file search) with its command‑line tool ES.exe available in your PATH.

📦 Installation
Clone the repository

bash
git clone https://github.com/yourusername/ray-assistant.git
cd ray-assistant
Create a virtual environment

bash
python -m venv .venv
.venv\Scripts\activate
Install dependencies

bash
pip install faster-whisper pyttsx3 speechrecognition pyaudio
pyaudio may need a wheel. If it fails, download the appropriate .whl from here and install manually.

(Optional) Setup Everything

Install Everything

Download ES.exe from the command‑line tools page

Place ES.exe in a folder that is in your PATH (e.g., C:\Windows\System32) or update the ES_PATH variable in the script.

🚀 Usage
Run the assistant:

bash
python ray.py
Once RAY speaks "Project RAY version 3 is online and ready", you have two ways to interact:

Push‑to‑talk voice
Press [ENTER] (with no text typed)

Speak your command clearly

RAY will transcribe and execute it

Typed commands
Simply type a command (e.g., open chrome) and press Enter

Exit
Type exit (or say "exit") to shut down RAY

🎤 Voice Commands Examples
You say (or type)	RAY does
open chrome	Launches Google Chrome
open spotify	Opens Spotify
open teams	Opens Microsoft Teams
search for annual report	Opens Everything window with that search
find file budget.xlsx	Opens Everything GUI (or direct open if configured)
open file readme.md	Opens the first matching file directly
everything cat.jpg	Opens Everything searching for cat.jpg
my code thing	Alias → opens VS Code
the inbox	Alias → opens Gmail in browser
🔧 Configuration
All settings are at the top of ray.py:

python
# Path to es.exe (Everything command line tool)
ES_PATH = "es.exe"

# If True, "open file X" opens the first match directly.
# If False, it opens Everything GUI with that search.
DIRECT_FILE_OPENING = True

# App commands and aliases
APP_COMMANDS = { ... }
ALIASES = { ... }
Adding a new app
Add an entry to APP_COMMANDS:

python
"open myapp": 'start "C:\\Path\\to\\app.exe"'
Adding a new voice alias
Add an entry to ALIASES:

python
"launch browser": "open chrome"
🎙️ Microphone Troubleshooting
If RAY doesn’t hear you:

Set your default microphone in Windows

Right‑click the speaker icon → Sounds → Recording

Right‑click your real mic → Set as Default Device

Update the microphone index in listen_for_command() (if you have many virtual devices)

python
# Find your mic index by running:
import speech_recognition as sr
for i, name in enumerate(sr.Microphone.list_microphone_names()):
    print(i, name)
Then set MIC_INDEX = your_index.

Switch to the sounddevice version (provided in the repository as ray_sounddevice.py) – this bypasses speech_recognition and works better with complex audio setups.

📁 File Structure
text
ray-assistant/
├── ray.py               # Main assistant with speech_recognition
├── ray_sounddevice.py   # Alternative using sounddevice (more robust)
├── README.md
└── requirements.txt
🧠 How It Works
Speech‑to‑text: faster-whisper (local, small model base.en)

Text‑to‑speech: pyttsx3 (offline)

App launching: Windows start command + direct .exe calls

File search: Uses es.exe to query the Everything database (if installed)

No internet required – everything runs locally

🛠️ Known Limitations
Everything integration requires ES.exe and Everything running in the background.

Voice recognition is push‑to‑talk; there is no continuous “wake word” yet.

The default speech_recognition library may conflict with virtual audio devices (Voicemeeter, Elgato). Use the sounddevice version if you encounter problems.

📜 License
MIT – feel free to use, modify, and share.

🤝 Contributing
Issues and pull requests are welcome. If you add support for Linux or macOS, please keep the Windows version intact.
