from jobfit.models import MatchResult
from jobfit.parse.resume import parse_resume
from jobfit.ingest.folder import ingest_folder
from jobfit.engine.embed import embed_profile, embed_jobs
from jobfit.engine.rank import rank_jobs
from jobfit.engine.judge import judge_jobs
from jobfit.cache.store import load_profile, save_profile, load_job_embeddings, save_job_embeddings

def run(
    resume_path: str, 
    jobs_dir: str, 
    top_k: int, 
    min_fit: int, 
    easy_apply_only: bool
) -> list[MatchResult]:
    """
    Orchestrates the matching pipeline from parsing to ranked JSON output.
    """
    # 1. Parse Resume (with caching)
    profile = load_profile(resume_path)
    if not profile:
        profile = parse_resume(resume_path)
        
    # 2. Ingest Jobs
    jobs = ingest_folder(jobs_dir)
    if not jobs:
        return []
        
    # 3. Embed
    embed_profile(profile)
    save_profile(resume_path, profile) # Save updated profile with embedding
    
    load_job_embeddings(jobs)
    embed_jobs(jobs)
    save_job_embeddings(jobs) # Save new job embeddings
    
    # 4. Rank
    top_jobs = rank_jobs(profile, jobs, top_k)
    
    # 5. Judge
    results = judge_jobs(profile, top_jobs)
    
    # 6. Filter
    filtered = []
    for r in results:
        if r.fit_score >= min_fit:
            if easy_apply_only and not r.job.easy_apply:
                continue
            filtered.append(r)
            
    # 7. Sort desc
    filtered.sort(key=lambda x: x.fit_score, reverse=True)
    
    return filtered
