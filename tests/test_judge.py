import json
from unittest.mock import patch
from jobfit.models import Profile, Job, MatchResult
from jobfit.engine.judge import judge_jobs

@patch("jobfit.engine.judge.chat")
def test_judge_jobs_parses_json(mock_chat):
    mock_chat.return_value = json.dumps({
        "fit_score": 85,
        "matched_skills": ["Python"],
        "missing_skills": ["Java"],
        "reason": "Good match overall."
    })
    
    profile = Profile("raw", ["Python"], 5, "Summary")
    job = Job("1", "Title", "Co", None, None, "Desc", None, True)
    
    results = judge_jobs(profile, [job])
    
    assert len(results) == 1
    assert results[0].fit_score == 85
    assert results[0].matched_skills == ["Python"]
    assert results[0].missing_skills == ["Java"]
    assert results[0].reason == "Good match overall."
