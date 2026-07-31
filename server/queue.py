import asyncio
from jobfit.config import MAX_CONCURRENT_LLM

# Global semaphore for LLM concurrency
llm_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM)
