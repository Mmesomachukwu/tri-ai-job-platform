"""
CV optimization (spec section 35-36). Uses the AI abstraction with the
same automatic Ollama-or-template fallback as analysis. Regardless of
which backend runs, the optimized content is stored alongside the
original CV text as a ResumeVersion, so a before/after comparison is
always possible and auditable - nothing here overwrites the original CV.
"""
from sqlalchemy.orm import Session
from app.models.resume import ResumeVersion
from app.repositories.resume_repository import ResumeRepository
from app.repositories.job_repository import JobRepository
from app.services.matching_service import calculate_match
from app.ai.factory import get_ai_service
from app.ai.ollama_service import OllamaUnavailableError, OllamaInvalidResponseError
from app.ai.template_service import TemplateAIService


def optimize_resume(db: Session, resume, job) -> ResumeVersion:
    job_repo = JobRepository(db)
    required, preferred = job_repo.get_skills(job.id)
    match_result = calculate_match(resume, job, required, preferred)

    job_context = {
        "title": job.title, "company": job.company,
        "responsibilities": job.responsibilities, "requirements": job.requirements,
    }

    ai_service, source = get_ai_service()
    try:
        optimization = ai_service.optimize_resume(resume.parsed_text or "", resume.parsed_data or {}, job_context, match_result)
    except (OllamaUnavailableError, OllamaInvalidResponseError):
        optimization = TemplateAIService().optimize_resume(resume.parsed_text or "", resume.parsed_data or {}, job_context, match_result)
        source = "template"

    content = {
        "original_text": resume.parsed_text,
        "optimized_summary": optimization.get("optimized_summary"),
        "bullet_changes": optimization.get("bullet_changes", []),
        "changes_explanation": optimization.get("changes_explanation"),
        "explanation_source": source,
        "based_on_score": match_result["overall_score"],
    }

    return ResumeRepository(db).create_version(
        resume_id=resume.id,
        job_id=job.id,
        version_name=f"Optimized for {job.title} @ {job.company}",
        content=content,
    )
