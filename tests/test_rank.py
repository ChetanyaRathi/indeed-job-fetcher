import numpy as np
from jobfit.models import Profile, Job
from jobfit.engine.rank import cosine_similarity, rank_jobs

def test_cosine_similarity():
    v1 = np.array([1, 0, 0])
    v2 = np.array([1, 0, 0])
    assert np.isclose(cosine_similarity(v1, v2), 1.0)
    
    v3 = np.array([0, 1, 0])
    assert np.isclose(cosine_similarity(v1, v3), 0.0)

def test_rank_jobs():
    profile = Profile("raw", ["Python"], 5, "Sum", embedding=[1.0, 0.0])
    job1 = Job("1", "Title 1", "Co", None, None, "Desc", None, True, embedding=[1.0, 0.0])
    job2 = Job("2", "Title 2", "Co", None, None, "Desc", None, True, embedding=[0.0, 1.0])
    
    jobs = [job2, job1] # 1 is best match, 2 is worst
    ranked = rank_jobs(profile, jobs, top_k=1)
    
    assert len(ranked) == 1
    assert ranked[0].id == "1"
