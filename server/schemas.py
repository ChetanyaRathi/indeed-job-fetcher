from pydantic import BaseModel
from typing import Optional

class JobCardSchema(BaseModel):
    title: str
    company: str
    location: Optional[str]
    salary: Optional[str]
    apply_url: Optional[str]
    easy_apply: bool
    source: str
    fit_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    reason: str

class MatchResponse(BaseModel):
    count: int
    corpus_size: int
    results: list[JobCardSchema]
