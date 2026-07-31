from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
import tempfile
from pathlib import Path
import asyncio

from jobfit.parse.resume import parse_resume
from jobfit.engine.embed import embed_profile
from jobfit.engine.rank import rank_jobs
from jobfit.engine.judge import judge_jobs
from jobfit.ingest.feeds import filter_jobs
from jobfit.config import TOP_K, MIN_FIT, EASY_APPLY_ONLY, MAX_UPLOAD_MB

from server.corpus import get_corpus, start_background_refresh
from server.queue import llm_semaphore
from server.schemas import MatchResponse, JobCardSchema

app = FastAPI(title="Indeed Job Fetcher API")

@app.on_event("startup")
async def startup_event():
    start_background_refresh()

@app.get("/health")
async def health():
    corpus = get_corpus()
    return {
        "status": "ok",
        "corpus_size": len(corpus)
    }

@app.post("/match", response_model=MatchResponse)
async def match_jobs(
    resume: UploadFile = File(...),
    roles: str = Form(""),
    location: str = Form(""),
    top_k: int = Form(TOP_K),
    min_fit: int = Form(MIN_FIT)
):
    corpus = get_corpus()
    if not corpus:
        raise HTTPException(status_code=503, detail="Job source not ready yet. Please try again in a few moments.")
        
    # Validate file size
    resume.file.seek(0, 2)
    file_size = resume.file.tell()
    resume.file.seek(0)
    if file_size > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Resume file exceeds maximum size of {MAX_UPLOAD_MB}MB")
        
    if not resume.filename.lower().endswith('.pdf') and not resume.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    # Process resume in temp file
    fd, temp_path = tempfile.mkstemp(suffix=Path(resume.filename).suffix)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(await resume.read())
            
        # 1. Parse & Embed (Fast)
        profile = parse_resume(temp_path)
        embed_profile(profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")
    finally:
        # Clean up resume file
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 2. Filter corpus
    role_list = [r.strip() for r in roles.split(",") if r.strip()]
    filtered_jobs = filter_jobs(corpus, role_list, location)
    
    # 3. Rank
    top_jobs = rank_jobs(profile, filtered_jobs, top_k)
    
    if not top_jobs:
        return MatchResponse(count=0, corpus_size=len(filtered_jobs), results=[])
        
    # 4. Judge (Slow, guarded by semaphore)
    async with llm_semaphore:
        # jobfit engine functions are sync, so we run them in a thread block
        try:
            results = await asyncio.to_thread(judge_jobs, profile, top_jobs)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Model server error: {str(e)}")

    # 5. Filter & Format
    final_results = []
    for r in results:
        if r.fit_score >= min_fit:
            if EASY_APPLY_ONLY and not r.job.easy_apply:
                continue
            final_results.append(
                JobCardSchema(
                    title=r.job.title,
                    company=r.job.company,
                    location=r.job.location,
                    salary=r.job.salary,
                    apply_url=r.job.apply_url,
                    easy_apply=r.job.easy_apply,
                    fit_score=r.fit_score,
                    matched_skills=r.matched_skills,
                    missing_skills=r.missing_skills,
                    reason=r.reason
                )
            )
            
    final_results.sort(key=lambda x: x.fit_score, reverse=True)
    
    return MatchResponse(
        count=len(final_results),
        corpus_size=len(filtered_jobs),
        results=final_results
    )

# Serve Frontend
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    async def index_fallback():
        return {"message": "Frontend not built yet. Run `npm run build` in the frontend directory."}
