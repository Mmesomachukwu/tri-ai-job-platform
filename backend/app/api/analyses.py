from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.job import Job
from app.schemas.analysis import AnalysisOut
from app.repositories.resume_repository import ResumeRepository
from app.services import analysis_service

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/resumes/{resume_id}/jobs/{job_id}", response_model=AnalysisOut)
def analyze(resume_id: str, job_id: str, db: Session = Depends(get_db)):
    resume = ResumeRepository(db).get(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    if resume.extraction_status != "success":
        raise HTTPException(400, "This resume could not be processed - upload a valid PDF or DOCX first.")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    return analysis_service.run_analysis(db, resume, job)


@router.get("/resumes/{resume_id}/jobs/{job_id}", response_model=AnalysisOut)
def get_analysis(resume_id: str, job_id: str, db: Session = Depends(get_db)):
    analysis = analysis_service.get_latest_analysis(db, resume_id, job_id)
    if not analysis:
        raise HTTPException(404, "No analysis yet - POST to this endpoint to generate one.")
    return analysis


@router.get("", response_model=list[AnalysisOut])
def list_my_analyses(db: Session = Depends(get_db)):
    return analysis_service.list_analyses(db)
