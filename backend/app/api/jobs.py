from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.job import JobOut, JobListResponse
from app.services import job_service, saved_job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
def list_jobs(
    keyword: str | None = None,
    category: str | None = None,
    location: str | None = None,
    remote_type: str | None = None,
    employment_type: str | None = None,
    experience_level: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    skills: str | None = None,  # comma-separated
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    skill_list = [s.strip() for s in skills.split(",")] if skills else None
    total, jobs = job_service.search_jobs(
        db, keyword=keyword, category=category, location=location,
        remote_type=remote_type, employment_type=employment_type,
        experience_level=experience_level, salary_min=salary_min, salary_max=salary_max,
        skills=skill_list, page=page, page_size=page_size,
    )
    return JobListResponse(total=total, page=page, page_size=page_size, results=jobs)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/sync")
def sync_jobs(query: str | None = None, db: Session = Depends(get_db)):
    """Pulls fresh real jobs from the configured JOB_PROVIDER into the
    database. Raises 503 (not a silent fallback) if the real provider is
    unreachable - see app/services/job_service.py:JobProviderUnavailableError."""
    try:
        return job_service.sync_jobs(db, query=query)
    except job_service.JobProviderUnavailableError as e:
        raise HTTPException(503, str(e))


saved_router = APIRouter(prefix="/saved-jobs", tags=["saved-jobs"])


@saved_router.post("/{job_id}")
def save_job(job_id: str, db: Session = Depends(get_db)):
    try:
        status = saved_job_service.save_job(db, job_id)
    except saved_job_service.SavedJobError as e:
        raise HTTPException(404, str(e))
    return {"status": status}


@saved_router.delete("/{job_id}")
def unsave_job(job_id: str, db: Session = Depends(get_db)):
    return {"status": saved_job_service.unsave_job(db, job_id)}


@saved_router.get("")
def list_saved_jobs(db: Session = Depends(get_db)):
    return saved_job_service.list_saved_jobs(db)
