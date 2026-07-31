from dataclasses import dataclass
from typing import Optional

@dataclass
class Profile:
    raw_text: str
    skills: list[str]
    experience_years: float
    summary: str
    embedding: Optional[list[float]] = None

@dataclass
class Job:
    id: str
    title: str
    company: str
    location: Optional[str]
    salary: Optional[str]
    description: str
    apply_url: Optional[str]
    easy_apply: bool
    embedding: Optional[list[float]] = None

@dataclass
class MatchResult:
    job: Job
    fit_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    reason: str
