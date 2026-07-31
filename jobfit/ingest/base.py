from jobfit.models import Job

def create_job(job_id: str, description: str, metadata: dict = None) -> Job:
    """
    Constructs a Job object. Merges metadata if provided, otherwise uses defaults.
    """
    metadata = metadata or {}
    
    # If no sidecar metadata provided, title defaults to the filename (job_id)
    # easy_apply defaults to True for folder ingestion as per Phase 1 specs.
    return Job(
        id=job_id,
        title=metadata.get("title", job_id),
        company=metadata.get("company", "Unknown"),
        location=metadata.get("location"),
        salary=metadata.get("salary"),
        description=description,
        apply_url=metadata.get("apply_url"),
        easy_apply=metadata.get("easy_apply", True),
        embedding=None
    )
