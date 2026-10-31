from sqlalchemy.orm import Session
from app.models.analysis import Analysis
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.job_repository import JobRepository
from app.services.matching_service import calculate_match
from app.ai.factory import get_ai_service
from app.ai.ollama_service import OllamaUnavailableError, OllamaInvalidResponseError
from app.ai.template_service import TemplateAIService


def run_analysis(db: Session, resume, job) -> Analysis:
    job_repo = JobRepository(db)
    required, preferred = job_repo.get_skills(job.id)

    match_result = calculate_match(resume, job, required, preferred)

    job_context = {
        "title": job.title, "company": job.company,
        "responsibilities": job.responsibilities, "requirements": job.requirements,
    }

    ai_service, source = get_ai_service()
    try:
        explanation = ai_service.analyze_resume(resume.parsed_text or "", job_context, match_result)
    except (OllamaUnavailableError, OllamaInvalidResponseError):
        # Defensive fallback: even if is_available() said yes moments ago,
        # the actual call can still fail (model unload, timeout, bad JSON).
        # Never surface that as a user-facing error - degrade to templates.
        explanation = TemplateAIService().analyze_resume(resume.parsed_text or "", job_context, match_result)
        source = "template"

    analysis_result = {
        "keyword_findings": [f.model_dump() for f in match_result["keyword_findings"]],
        "experience_findings": [f.model_dump() for f in match_result["experience_findings"]],
        "education_findings": [f.model_dump() for f in match_result["education_findings"] if f],
        "responsibility_alignment": match_result["responsibility_alignment"],
        "structure_notes": match_result["structure_notes"],
    }

    return AnalysisRepository(db).create(
        resume_id=resume.id,
        job_id=job.id,
        overall_score=match_result["overall_score"],
        skills_score=match_result["skills_score"],
        keyword_score=match_result["keyword_score"],
        experience_score=match_result["experience_score"],
        education_score=match_result["education_score"],
        responsibility_score=match_result["responsibility_score"],
        structure_score=match_result["structure_score"],
        semantic_score=match_result["semantic_score"],
        analysis_result=analysis_result,
        recommendations=explanation["recommendations"],
        explanation_source=source,
    )


def get_latest_analysis(db: Session, resume_id: str, job_id: str) -> Analysis | None:
    return AnalysisRepository(db).get_latest(resume_id, job_id)


def list_analyses(db: Session, limit: int = 20) -> list[Analysis]:
    return AnalysisRepository(db).list_all(limit)
