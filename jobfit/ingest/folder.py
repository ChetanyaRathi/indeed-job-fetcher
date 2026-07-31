import json
from pathlib import Path
from jobfit.models import Job
from jobfit.ingest.base import create_job

def ingest_folder(folder_path: str | Path) -> list[Job]:
    """
    Reads all .txt files in the given folder as job descriptions.
    Looks for matching .json files for metadata.
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise NotADirectoryError(f"Job folder not found: {folder_path}")

    jobs = []
    
    for txt_file in folder.glob("*.txt"):
        job_id = txt_file.stem
        
        with open(txt_file, "r", encoding="utf-8") as f:
            description = f.read().strip()
            
        if not description:
            continue
            
        metadata = {}
        json_file = folder / f"{job_id}.json"
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to parse {json_file.name}: {e}")
                
        job = create_job(job_id, description, metadata)
        jobs.append(job)
        
    return jobs
