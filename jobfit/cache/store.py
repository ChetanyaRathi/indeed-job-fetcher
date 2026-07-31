import os
import json
import hashlib
from pathlib import Path
from dataclasses import asdict
from jobfit.models import Profile, Job
from jobfit.config import DATA_DIR

CACHE_DIR = Path(DATA_DIR) / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _hash_file(file_path: str) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def _hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_profile(file_path: str) -> Profile | None:
    try:
        file_hash = _hash_file(file_path)
        cache_path = CACHE_DIR / f"profile_{file_hash}.json"
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Profile(**data)
    except Exception as e:
        print(f"Warning: Cache load error for profile: {e}")
    return None

def save_profile(file_path: str, profile: Profile):
    try:
        file_hash = _hash_file(file_path)
        cache_path = CACHE_DIR / f"profile_{file_hash}.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(asdict(profile), f, indent=2)
    except Exception as e:
        print(f"Warning: Cache save error for profile: {e}")

def load_job_embeddings(jobs: list[Job]):
    for job in jobs:
        try:
            job_hash = _hash_text(job.description)
            cache_path = CACHE_DIR / f"job_{job_hash}.json"
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    job.embedding = data.get("embedding")
        except Exception:
            pass

def save_job_embeddings(jobs: list[Job]):
    for job in jobs:
        if not job.embedding:
            continue
        try:
            job_hash = _hash_text(job.description)
            cache_path = CACHE_DIR / f"job_{job_hash}.json"
            if not cache_path.exists():
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump({"embedding": job.embedding}, f)
        except Exception:
            pass
