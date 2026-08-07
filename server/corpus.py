import asyncio
from typing import List
from jobfit.models import Job
from jobfit.ingest.feeds import fetch_all
from jobfit.engine.embed import embed_jobs
from jobfit.cache.store import load_job_embeddings, save_job_embeddings
from jobfit.config import JOB_REFRESH_HOURS

global_corpus: List[Job] = []
_refresh_task = None

def get_corpus() -> List[Job]:
    return global_corpus

def _update_corpus_sync():
    global global_corpus
    print("Fetching jobs from Adzuna...")
    jobs = fetch_all()
    print(f"Fetched {len(jobs)} jobs. Loading cache...")
    load_job_embeddings(jobs)
    
    print("Embedding jobs (only missing embeddings will be computed)...")
    embed_jobs(jobs)
    
    print("Saving embeddings to cache...")
    save_job_embeddings(jobs)
    
    global_corpus = jobs
    print(f"Corpus refresh complete. {len(global_corpus)} jobs in memory.")

async def refresh_corpus():
    await asyncio.to_thread(_update_corpus_sync)

async def _refresh_loop():
    while True:
        try:
            await refresh_corpus()
        except Exception as e:
            print(f"Error refreshing corpus: {e}")
        # If the corpus is still empty (e.g. Adzuna was down), retry soon
        # instead of waiting the full refresh interval and staying broken.
        if not global_corpus:
            print("Corpus empty after refresh; retrying in 60s.")
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(JOB_REFRESH_HOURS * 3600)

def start_background_refresh():
    global _refresh_task
    if _refresh_task is None:
        _refresh_task = asyncio.create_task(_refresh_loop())
