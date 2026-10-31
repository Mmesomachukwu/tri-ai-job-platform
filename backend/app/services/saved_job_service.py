from sqlalchemy.orm import Session
from app.repositories.job_repository import JobRepository, SavedJobRepository


class SavedJobError(Exception):
    pass


def save_job(db: Session, job_id: str) -> str:
    if not JobRepository(db).get(job_id):
        raise SavedJobError("Job not found")
    repo = SavedJobRepository(db)
    if repo.get_for_job(job_id):
        return "already_saved"
    repo.create(job_id=job_id)
    return "saved"


def unsave_job(db: Session, job_id: str) -> str:
    repo = SavedJobRepository(db)
    existing = repo.get_for_job(job_id)
    if existing:
        repo.delete(existing)
    return "removed"


def list_saved_jobs(db: Session):
    return SavedJobRepository(db).list_jobs()
