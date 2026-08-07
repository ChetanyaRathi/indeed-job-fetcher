import os
from dotenv import load_dotenv

load_dotenv()

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5:9b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
TOP_K = int(os.getenv("TOP_K", "10"))
MIN_FIT = int(os.getenv("MIN_FIT", "75"))
# Adzuna jobs redirect to external ATS forms (never "easy apply"), so this
# defaults to false; leaving it true would drop every job from the results.
EASY_APPLY_ONLY = os.getenv("EASY_APPLY_ONLY", "false").lower() in ("true", "1", "yes")
MAX_CONCURRENT_LLM = int(os.getenv("MAX_CONCURRENT_LLM", "1"))
JOB_REFRESH_HOURS = int(os.getenv("JOB_REFRESH_HOURS", "6"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))

DATA_DIR = os.getenv("DATA_DIR", "data")

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "us")
ADZUNA_TARGET_COUNT = int(os.getenv("ADZUNA_TARGET_COUNT", "100"))
