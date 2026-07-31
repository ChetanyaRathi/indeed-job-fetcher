import httpx
import re
from typing import Optional
from jobfit.models import Job
import html

def strip_html(text: Optional[str]) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

def fetch_greenhouse(token: str) -> list[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    jobs = []
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        for item in data.get("jobs", []):
            job = Job(
                id=str(item.get("id")),
                title=item.get("title", ""),
                company=token,  # Or somehow extract company if available
                location=item.get("location", {}).get("name", ""),
                salary=None, # Greenhouse API doesn't cleanly expose salary in the list endpoint usually
                description=strip_html(item.get("content", "")),
                apply_url=item.get("absolute_url", ""),
                easy_apply=True,
                embedding=None
            )
            jobs.append(job)
    except Exception as e:
        print(f"Error fetching Greenhouse {token}: {e}")
    return jobs

def fetch_lever(token: str) -> list[Job]:
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    jobs = []
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        for item in data:
            job = Job(
                id=str(item.get("id")),
                title=item.get("text", ""),
                company=token,
                location=item.get("categories", {}).get("location", ""),
                salary=None,
                description=item.get("descriptionPlain", ""),
                apply_url=item.get("hostedUrl", ""),
                easy_apply=True,
                embedding=None
            )
            jobs.append(job)
    except Exception as e:
        print(f"Error fetching Lever {token}: {e}")
    return jobs

def fetch_ashby(token: str) -> list[Job]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"
    jobs = []
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        for item in data.get("jobs", []):
            desc = item.get("descriptionPlain") or strip_html(item.get("description", ""))
            job = Job(
                id=str(item.get("id")),
                title=item.get("title", ""),
                company=token,
                location=item.get("location", ""),
                salary=None, # Compensation might be present but format varies, leaving None for now
                description=desc,
                apply_url=item.get("applyUrl") or item.get("jobUrl", ""),
                easy_apply=True,
                embedding=None
            )
            # Try to parse salary if it exists
            comp = item.get("compensation", {})
            if comp and isinstance(comp, dict):
                min_comp = comp.get("compensationTierMin")
                max_comp = comp.get("compensationTierMax")
                currency = comp.get("currencyCode", "USD")
                if min_comp and max_comp:
                    job.salary = f"{min_comp} - {max_comp} {currency}"
            
            jobs.append(job)
    except Exception as e:
        print(f"Error fetching Ashby {token}: {e}")
    return jobs
