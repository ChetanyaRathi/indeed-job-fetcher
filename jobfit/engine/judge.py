import json
from pathlib import Path
from jobfit.models import Profile, Job, MatchResult
from jobfit.llm.client import chat_no_think


def _slice_json(text: str) -> str:
    """Strip markdown fences and slice from the first { to the last }."""
    text = (text or "").strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end + 1]
    return text


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
        
        # The prompt template contains literal JSON braces, so use targeted
        # placeholder replacement instead of str.format() (which would treat
        # every { in the example JSON as a format field and raise KeyError).
        prompt = prompt_template.replace("{resume}", profile_text).replace("{job}", job_text)
        messages = [{"role": "user", "content": prompt}]
        
        success = False
        for attempt in range(2):
            response_json = ""
            try:
                # qwen3.5 is a thinking model; on the OpenAI-compat endpoint it
                # ignores the think flag and burns the token budget reasoning,
                # truncating the JSON. The native no-think path returns clean JSON.
                resp = chat_no_think(messages, max_tokens=1200)
                response_json = (resp.get("message", {}) or {}).get("content") or ""
                sliced = _slice_json(response_json)
                data = json.loads(sliced)
                
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
                success = True
                break
            except Exception as e:
                print(f"Warning: Failed to judge job {job.id} on attempt {attempt + 1}: {e}")
                if 'response_json' in locals():
                    print(f"Raw response was: {response_json}")
                
        if not success:
            print(f"Error: Skipping job {job.id} after 2 failed attempts.")
            
    return results
