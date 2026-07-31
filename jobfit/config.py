import os
from dotenv import load_dotenv

load_dotenv()

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5:9b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
TOP_K = int(os.getenv("TOP_K", "10"))
MIN_FIT = int(os.getenv("MIN_FIT", "75"))
EASY_APPLY_ONLY = os.getenv("EASY_APPLY_ONLY", "true").lower() in ("true", "1", "yes")
MAX_CONCURRENT_LLM = int(os.getenv("MAX_CONCURRENT_LLM", "1"))
JOB_REFRESH_HOURS = int(os.getenv("JOB_REFRESH_HOURS", "6"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))

DATA_DIR = os.getenv("DATA_DIR", "data")
