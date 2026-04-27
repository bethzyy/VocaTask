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
CRM_PORT = 8011
HOST = "0.0.0.0"
MAX_AUDIO_SIZE_MB = 50

# === ZhipuAI ===
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "").strip()

# === AI Models ===
ASR_MODEL = "GLM-ASR-2512"
ROUTING_MODEL = "glm-4-flash"
API_TIMEOUT = 30

# === Audio Processing ===
SUPPORTED_AUDIO_EXT = {".wav", ".webm", ".mp3", ".ogg", ".m4a", ".flac"}
SEGMENT_DURATION = 25  # seconds for long-form chunking

# === Image Processing ===
IMAGE_DIR = DATA_DIR / "images"
MAX_IMAGE_SIZE_MB = 10
SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VISION_MODEL = "glm-4v-flash"
MAX_IMAGES_PER_TASK = 5

# === Claude API ===
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")

# === AI Task Analysis (Anthropic-compatible) ===
AI_ROUTER_BASE_URL = "https://open.bigmodel.cn/api/anthropic"
AI_ROUTER_API_KEY = os.environ.get("ZHIPU_API_KEY", "").strip()
AI_ROUTER_MODEL = "glm-4-flash"

# === FFmpeg ===
FFMPEG_PATH = Path(os.environ.get("FFMPEG_PATH", "ffmpeg"))


def ensure_dirs():
    """Create runtime directories if they don't exist."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
