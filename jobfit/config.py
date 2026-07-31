import os
from dotenv import load_dotenv

load_dotenv()

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5:9b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
TOP_K = int(os.getenv("TOP_K", "10"))
MIN_FIT = int(os.getenv("MIN_FIT", "75"))
EASY_APPLY_ONLY = os.getenv("EASY_APPLY_ONLY", "true").lower() in ("true", "1", "yes")

DATA_DIR = os.getenv("DATA_DIR", "data")
