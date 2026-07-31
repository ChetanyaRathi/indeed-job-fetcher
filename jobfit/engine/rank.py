import numpy as np
from jobfit.models import Profile, Job

def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def rank_jobs(profile: Profile, jobs: list[Job], top_k: int) -> list[Job]:
    """
    Ranks jobs against the profile using cosine similarity on embeddings.
    Returns the top_k scoring jobs.
    """
    if not profile.embedding or not jobs:
        return []
        
    scored_jobs = []
    p_emb = np.array(profile.embedding)
    
    for job in jobs:
        if job.embedding:
            j_emb = np.array(job.embedding)
            score = cosine_similarity(p_emb, j_emb)
            scored_jobs.append((score, job))
            
    # Sort descending
    scored_jobs.sort(key=lambda x: x[0], reverse=True)
    
    # Return top K jobs
    return [job for score, job in scored_jobs[:top_k]]
