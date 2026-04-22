import os
from pathlib import Path

# === Project Paths ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "help.db"
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"

# === Server ===
PORT = 8010
HOST = "0.0.0.0"
MAX_AUDIO_SIZE_MB = 50

# === ZhipuAI ===
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "").strip()
if not ZHIPU_API_KEY:
    key_file = Path(r"C:\D\CAIE_tool\LLM_Configs\GLM\apikeyValue2.txt")
    if key_file.exists():
        ZHIPU_API_KEY = key_file.read_text(encoding="utf-8").strip()

# === AI Models ===
ASR_MODEL = "GLM-ASR-2512"
ROUTING_MODEL = "glm-4-flash"
API_TIMEOUT = 30

# === Audio Processing ===
SUPPORTED_AUDIO_EXT = {".wav", ".webm", ".mp3", ".ogg", ".m4a", ".flac"}
SEGMENT_DURATION = 25  # seconds for long-form chunking

# === FFmpeg ===
FFMPEG_PATH = Path(
    r"C:\D\CAIE_tool\MyAIProduct\gethtml\ffmpeg_temp"
    r"\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"
)


def ensure_dirs():
    """Create runtime directories if they don't exist."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
