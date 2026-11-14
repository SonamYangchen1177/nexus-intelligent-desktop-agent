
from pathlib import Path
import logging

# Project root directory
BASE_DIR = Path(__file__).resolve().parent

# Safe workspace for initial file operations
WORKSPACE = BASE_DIR / "workspace"

# Other project directories
LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:8b"

# Agent configuration
MAX_RETRIES = 2
MAX_PLAN_STEPS = 15

# Safety configuration
REQUIRE_CONFIRMATION = True
ALLOW_PERMANENT_DELETE = False

# Create required directories if they do not exist
for directory in [WORKSPACE, LOG_DIR, REPORT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOG_FILE = LOG_DIR / "agent.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)