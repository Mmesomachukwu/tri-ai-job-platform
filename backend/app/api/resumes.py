from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.job import Job
from app.schemas.resume import ResumeOut, ResumeVersionOut
from app.services import resume_service, optimization_service
from app.repositories.resume_repository import ResumeRepository

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    label: str | None = Form(None),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    try:
        resume = resume_service.upload_and_process_resume(db, file.filename, file_bytes, label)
    except resume_service.ResumeValidationError as e:
        raise HTTPException(400, str(e))
    return resume


@router.get("", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db)):
    return ResumeRepository(db).list_all()


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: str, db: Session = Depends(get_db)):
    resume = ResumeRepository(db).get(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    return resume


@router.delete("/{resume_id}")
def delete_resume(resume_id: str, db: Session = Depends(get_db)):
    repo = ResumeRepository(db)
    resume = repo.get(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    repo.delete(resume)
    return {"status": "deleted"}


@router.post("/{resume_id}/optimize/{job_id}", response_model=ResumeVersionOut)
def optimize_resume(resume_id: str, job_id: str, db: Session = Depends(get_db)):
    resume = ResumeRepository(db).get(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    if resume.extraction_status != "success":
        raise HTTPException(400, "This resume could not be processed - upload a valid PDF or DOCX first.")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    return optimization_service.optimize_resume(db, resume, job)


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionOut])
def list_versions(resume_id: str, db: Session = Depends(get_db)):
    repo = ResumeRepository(db)
    resume = repo.get(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    return repo.list_versions(resume_id)
