from jobfit.models import Profile, Job
from jobfit.llm.client import embed

def embed_profile(profile: Profile):
    """
    Embeds the candidate profile if not already embedded.
    """
    if not profile.embedding:
        text = f"{profile.summary}\nSkills: {', '.join(profile.skills)}"
        res = embed([text])
        if res:
            profile.embedding = res[0]

def embed_jobs(jobs: list[Job]):
    """
    Embeds any jobs that lack an embedding.
    """
    jobs_to_embed = [j for j in jobs if not j.embedding]
    if not jobs_to_embed:
        return
        
    texts = [f"{j.title}\n{j.description}" for j in jobs_to_embed]
    embeddings = embed(texts)
    
    for job, emb in zip(jobs_to_embed, embeddings):
        job.embedding = emb
