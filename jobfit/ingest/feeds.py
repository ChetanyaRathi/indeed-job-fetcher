from typing import Optional
from jobfit.models import Job
from jobfit.ingest.ats import fetch_greenhouse, fetch_lever, fetch_ashby

# Placeholder boards list. Users will replace these with real tokens.
BOARDS = [
    ("greenhouse", "openai"),
    ("lever", "netflix"),
    ("ashby", "notion"),
    # Add more placeholders as needed
    ("greenhouse", "airbnb"),
    ("lever", "spotify"),
]

def fetch_all() -> list[Job]:
    """
    Fetches jobs from all boards in the BOARDS list.
    Deduplicates by apply URL.
    """
    all_jobs = []
    seen_urls = set()
    
    for provider, token in BOARDS:
        jobs = []
        if provider == "greenhouse":
            jobs = fetch_greenhouse(token)
        elif provider == "lever":
            jobs = fetch_lever(token)
        elif provider == "ashby":
            jobs = fetch_ashby(token)
            
        for j in jobs:
            if j.apply_url and j.apply_url not in seen_urls:
                all_jobs.append(j)
                seen_urls.add(j.apply_url)
                
    return all_jobs

def filter_jobs(jobs: list[Job], roles: list[str], location: Optional[str] = None) -> list[Job]:
    """
    Filters the job list by role keywords and location.
    - roles: list of keywords to match in title (case-insensitive).
    - location: substring match in location (case-insensitive), pass-through if empty.
    """
    if not roles and not location:
        return jobs
        
    filtered = []
    for j in jobs:
        title_lower = j.title.lower() if j.title else ""
        loc_lower = j.location.lower() if j.location else ""
        
        role_match = False
        if roles:
            for r in roles:
                if r.lower() in title_lower:
                    role_match = True
                    break
        else:
            role_match = True # If no roles specified, it's a match
            
        loc_match = False
        if location:
            if location.lower() in loc_lower:
                loc_match = True
        else:
            loc_match = True
            
        if role_match and loc_match:
            filtered.append(j)
            
    return filtered
