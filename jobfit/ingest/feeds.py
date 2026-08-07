import re
import time
import logging
import json
import urllib.request
import urllib.parse
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone, timedelta
from typing import Optional
from jobfit.models import Job
from jobfit.config import ADZUNA_APP_ID, ADZUNA_APP_KEY, ADZUNA_COUNTRY, ADZUNA_TARGET_COUNT

logger = logging.getLogger(__name__)


def _get_json_with_retry(url: str, retries: int = 3, timeout: int = 20) -> Optional[dict]:
    """
    GET a URL and parse JSON, retrying transient failures (503/429/5xx/network)
    with exponential backoff. Returns the parsed dict, or None if all attempts
    fail. Adzuna's free tier intermittently returns 503, so a single hiccup must
    not wipe the whole corpus.
    """
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "jobfit/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            transient = e.code in (429, 500, 502, 503, 504)
            logger.error("Adzuna HTTP %s (attempt %d/%d)%s",
                         e.code, attempt + 1, retries, " - retrying" if transient else "")
            if not transient:
                return None
        except (URLError, ConnectionError, TimeoutError, json.JSONDecodeError) as e:
            # Includes RemoteDisconnected ("Remote end closed connection"),
            # which Adzuna throws under load — retry rather than abort the fetch.
            logger.error("Adzuna request error (attempt %d/%d): %s", attempt + 1, retries, e)
        if attempt < retries - 1:
            time.sleep(2 ** attempt)  # 1s, 2s, 4s
    return None

# Location queries that should match broadly rather than by exact substring.
_BROAD_LOCATIONS = {"united states", "us", "u.s.", "u.s", "usa", "america", "remote", "anywhere"}


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens, keeping tech chars like + and #."""
    return [w for w in re.split(r"[^a-z0-9+#]+", (text or "").lower()) if w]


def _role_tokens(roles: list[str]) -> set[str]:
    """Build a forgiving token set from role keywords."""
    tokens: set[str] = set()
    for r in roles or []:
        phrase = (r or "").strip().lower()
        if not phrase:
            continue
        tokens.add(phrase)
        for w in _tokenize(phrase):
            if len(w) >= 2:
                tokens.add(w)
    return tokens


def _title_matches_roles(title: str, tokens: set[str]) -> bool:
    """A title passes if ANY role token matches it."""
    title_lower = (title or "").lower()
    title_words = _tokenize(title_lower)
    for tok in tokens:
        if tok in title_lower:
            return True
        for tw in title_words:
            if len(tw) >= 3 and len(tok) >= 3 and (tok in tw or tw in tok):
                return True
    return False


def _location_matches(job_location: Optional[str], location: Optional[str]) -> bool:
    """Loose, case-insensitive location match; blank query matches everything."""
    query = (location or "").strip().lower()
    if not query:
        return True
    if query in _BROAD_LOCATIONS:
        return True
    return query in (job_location or "").lower()


# Title markers used to infer a posting's seniority.
_SENIOR_KW = ("senior", "sr.", "sr ", "staff", "principal", "lead", "architect",
              "director", "head of", "vp ", "distinguished", "manager", " iii", " iv")
_JUNIOR_KW = ("junior", "jr.", "jr ", "intern", "trainee", "new grad", "new-grad",
              "graduate", "entry level", "entry-level", "apprentice")


def _seniority_matches(title: str, level: Optional[str]) -> bool:
    """
    Loose title-based seniority filter.
    - 'senior': only senior-marked titles.
    - 'mid':    exclude senior- and junior-marked titles (plain roles).
    - 'entry':  exclude senior-marked titles (keep junior + unmarked roles,
                since most entry roles are just titled "Software Engineer").
    - 'any'/blank: everything.
    """
    lvl = (level or "").strip().lower()
    if not lvl or lvl in ("any", "all"):
        return True
    t = " " + (title or "").lower() + " "
    has_senior = any(k in t for k in _SENIOR_KW)
    has_junior = any(k in t for k in _JUNIOR_KW)
    if lvl == "senior":
        return has_senior
    if lvl == "mid":
        return not has_senior and not has_junior
    if lvl == "entry":
        return not has_senior
    return True


def _dedup_key(title: str, company: str, description: str = "") -> str:
    """
    Key used to collapse the SAME role listed across many cities. Adzuna returns
    one job per location with a distinct redirect_url (and even a slightly
    different description snippet per city), so URL- or description-based dedup
    lets identical roles flood the results. Keying on title+company collapses
    them to a single card, which is what a user perceives as one job.
    """
    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").strip().lower())
    return f"{norm(title)}|{norm(company)}"


def fetch_all(
    what: str = "software engineer",
    where: str = "united states",
    max_days_old: int = 7,
    target: Optional[int] = None,
) -> list[Job]:
    """
    Fetch jobs from Adzuna for a given search query.

    ``what`` is the keyword query (e.g. the user's target role), so the pool
    that gets ranked is actually relevant to them instead of a generic
    "software engineer" pull. Deduplicates by apply URL AND by content key
    (title+company+description) so the same role across multiple cities does
    not appear as several near-identical cards.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("ADZUNA_APP_ID or ADZUNA_APP_KEY is not configured correctly.")
        return []

    target = target or ADZUNA_TARGET_COUNT
    all_jobs = []
    seen_urls = set()
    seen_keys = set()
    country = ADZUNA_COUNTRY or "us"

    # Enough pages (50/page) to reach the target, capped so we don't loop forever.
    per_page = 50
    num_pages = min(10, max(1, -(-target // per_page)))

    for page in range(1, num_pages + 1):
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": str(per_page),
            "what": what or "software engineer",
            "where": where or "united states",
            "max_days_old": str(max_days_old),
            "sort_by": "date",
            "content-type": "application/json"
        }
        
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?" + urllib.parse.urlencode(params)

        data = _get_json_with_retry(url)
        if data is None:
            # Transient failure on this page; try the next one rather than
            # abandoning the whole fetch (which would leave the corpus empty).
            continue

        try:
            jobs_data = data.get("results", [])
            if not jobs_data:
                break

            for j in jobs_data:
                apply_url = j.get("redirect_url")
                title = j.get("title", "")
                company = j.get("company", {}).get("display_name", "Unknown")
                location = j.get("location", {}).get("display_name", "")
                description = j.get("description", "")

                if not apply_url or apply_url in seen_urls:
                    continue
                key = _dedup_key(title, company, description)
                if key in seen_keys:
                    continue
                seen_urls.add(apply_url)
                seen_keys.add(key)

                job = Job(
                    id=str(j.get("id", "")),
                    title=title,
                    company=company,
                    location=location,
                    salary=None,
                    description=description,
                    apply_url=apply_url,
                    easy_apply=False,
                    source="Adzuna",
                    posted_at=j.get("created")
                )
                all_jobs.append(job)
                if len(all_jobs) >= target:
                    break
        except Exception as e:
            logger.error(f"Error parsing Adzuna page {page}: {e}")
            continue

        if len(all_jobs) >= target:
            break

    logger.info("Adzuna fetch complete for %r: %d unique jobs", what, len(all_jobs))
    return all_jobs


def fetch_for_roles(
    roles: list[str],
    where: str = "united states",
    max_days_old: int = 7,
    target: Optional[int] = None,
) -> list[Job]:
    """
    Fetch a candidate pool tailored to the user's target roles.

    Fetches once per role (so "Machine Learning Engineer" and "AI Engineer"
    each contribute their own results) and merges with cross-role dedup. Falls
    back to the generic query when no roles are supplied.
    """
    target = target or ADZUNA_TARGET_COUNT
    roles = [r for r in (roles or []) if r.strip()][:4]  # cap API calls
    if not roles:
        return fetch_all(where=where, max_days_old=max_days_old, target=target)

    merged: list[Job] = []
    seen_urls: set[str] = set()
    seen_keys: set[str] = set()
    per_role = max(30, -(-target // len(roles)))

    for role in roles:
        for job in fetch_all(what=role, where=where, max_days_old=max_days_old, target=per_role):
            if not job.apply_url or job.apply_url in seen_urls:
                continue
            key = _dedup_key(job.title, job.company, job.description)
            if key in seen_keys:
                continue
            seen_urls.add(job.apply_url)
            seen_keys.add(key)
            merged.append(job)
            if len(merged) >= target:
                break
        if len(merged) >= target:
            break

    logger.info("fetch_for_roles %s -> %d unique jobs", roles, len(merged))
    return merged


def parse_posted_at(posted_at: Optional[str]) -> Optional[datetime]:
    if not posted_at:
        return None
    try:
        # e.g. "2023-09-01T12:00:00.000Z"
        if posted_at.endswith('Z'):
            posted_at = posted_at[:-1] + '+00:00'
        dt = datetime.fromisoformat(posted_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def filter_jobs(
    jobs: list[Job], 
    roles: list[str], 
    location: Optional[str] = None,
    window: str = "1w",
    seniority: Optional[str] = None,
) -> list[Job]:
    """
    Filter the job list by role keywords, location, date window, and seniority.
    window: '1d', '3d', '1w'; seniority: 'entry'/'mid'/'senior'/'any'.
    """
    tokens = _role_tokens(roles)
    
    # Calculate cutoff date based on window
    now = datetime.now(timezone.utc)
    cutoff = None
    if window == "1d":
        cutoff = now - timedelta(days=1)
    elif window == "3d":
        cutoff = now - timedelta(days=3)
    elif window == "1w":
        cutoff = now - timedelta(days=7)

    role_pass = 0
    loc_pass = 0
    date_pass = 0
    sen_pass = 0
    filtered = []
    
    for j in jobs:
        # Check date
        if cutoff and j.posted_at:
            dt = parse_posted_at(j.posted_at)
            if dt and dt < cutoff:
                continue
        date_pass += 1
            
        role_match = True if not tokens else _title_matches_roles(j.title, tokens)
        loc_match = _location_matches(j.location, location)
        sen_match = _seniority_matches(j.title, seniority)

        if role_match:
            role_pass += 1
        if loc_match:
            loc_pass += 1
        if sen_match:
            sen_pass += 1
            
        if role_match and loc_match and sen_match:
            filtered.append(j)

    logger.info(
        "filter_jobs: %d jobs -> date %d, role %d, location %d, seniority %d, combined %d",
        len(jobs), date_pass, role_pass, loc_pass, sen_pass, len(filtered)
    )

    if not filtered:
        logger.info("filter_jobs: no jobs matched; falling back to full date-filtered corpus")
        # If we fallback, we should at least maintain date filtering
        fallback = [j for j in jobs if 
                    (not cutoff or (j.posted_at and parse_posted_at(j.posted_at) and parse_posted_at(j.posted_at) >= cutoff))]
        return fallback

    return filtered
