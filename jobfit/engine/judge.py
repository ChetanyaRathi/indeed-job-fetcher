import json
from pathlib import Path
from jobfit.models import Profile, Job, MatchResult
from jobfit.llm.client import chat

def judge_jobs(profile: Profile, top_jobs: list[Job]) -> list[MatchResult]:
    """
    Uses the LLM to judge a pre-filtered list of top jobs against the profile.
    """
    prompt_path = Path(__file__).parent.parent / "prompts" / "judge.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
        
    profile_text = (
        f"Summary:\n{profile.summary}\n\n"
        f"Skills:\n{', '.join(profile.skills)}\n\n"
        f"Experience: {profile.experience_years} years"
    )
    
    results = []
    for job in top_jobs:
        job_text = (
            f"Title: {job.title}\n"
            f"Company: {job.company}\n"
            f"Description:\n{job.description}"
        )
        
        prompt = prompt_template.format(resume=profile_text, job=job_text)
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response_json = chat(messages, response_format={"type": "json_object"})
            data = json.loads(response_json)
            
            fit_score = int(data.get("fit_score", 0))
            matched = data.get("matched_skills", [])
            missing = data.get("missing_skills", [])
            reason = data.get("reason", "No reason provided.")
            
            result = MatchResult(
                job=job,
                fit_score=fit_score,
                matched_skills=matched,
                missing_skills=missing,
                reason=reason
            )
            results.append(result)
        except Exception as e:
            print(f"Warning: Failed to judge job {job.id}: {e}")
            
    return results
