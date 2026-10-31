"""
Deterministic ATS-style scoring engine (spec sections 12-19).

CRITICAL: the score is never produced by an LLM. Every subscore here is
computed from measurable signals. The AI layer (app/ai/ollama_service.py)
only ever explains an already-computed score - it cannot influence it.
"""
from app.database.config import settings
from app.ai.skill_taxonomy import (
    extract_technical_skills, education_rank, extract_education_level,
    find_evidence_snippet,
)
from app.ai.embedding_service import similarity
from app.schemas.analysis import KeywordFinding, QualificationFinding


def _skills_scoring(cv_text: str, cv_skills: list[str], required: list[str], preferred: list[str]) -> dict:
    cv_set = {s.lower() for s in cv_skills}
    matched_required = [s for s in required if s in cv_set]
    missing_required = [s for s in required if s not in cv_set]
    matched_preferred = [s for s in preferred if s in cv_set]

    req_score = len(matched_required) / len(required) if required else 1.0
    pref_score = len(matched_preferred) / len(preferred) if preferred else 1.0
    score = 0.8 * req_score + 0.2 * pref_score

    findings = []
    for skill in matched_required + matched_preferred:
        evidence = find_evidence_snippet(skill, cv_text) or skill
        findings.append(KeywordFinding(term=skill, status="demonstrated", cv_evidence=evidence))
    for skill in missing_required:
        findings.append(KeywordFinding(term=skill, status="gap"))

    return {"score": round(score * 100, 1), "findings": findings,
            "matched_required": matched_required, "missing_required": missing_required}


def _keyword_scoring(cv_text: str, job_text: str, cv_skills: list[str]) -> dict:
    """Extracts important terms from the job description/requirements
    (spec section 15) and checks presence in the CV, independent of the
    structured required/preferred skill lists (catches terminology in
    free text that isn't in the structured skill fields)."""
    job_terms = extract_technical_skills(job_text)
    cv_set = {s.lower() for s in cv_skills}
    found = [t for t in job_terms if t in cv_set]
    not_found = [t for t in job_terms if t not in cv_set]
    score = len(found) / len(job_terms) if job_terms else 1.0
    return {"score": round(score * 100, 1), "found": found, "not_found": not_found}


def _experience_scoring(cv_text: str, cv_years: float | None, job_min_years: float | None,
                         job_responsibilities: str) -> dict:
    if not job_min_years:
        years_score = 1.0
        explanation = "No specific years-of-experience requirement was stated in the job posting."
    elif cv_years is None:
        years_score = 0.4
        explanation = f"The job requests approximately {job_min_years:g}+ years of experience; a clear figure could not be identified in your CV."
    else:
        years_score = min(1.0, cv_years / job_min_years)
        explanation = f"The job requests approximately {job_min_years:g}+ years of experience; your CV demonstrates approximately {cv_years:g} years."

    relevance = similarity(cv_text, job_responsibilities)
    score = 0.6 * years_score + 0.4 * relevance

    status = "met" if years_score >= 1.0 else ("partial" if years_score >= 0.5 else "not_demonstrated")
    finding = QualificationFinding(label=f"{job_min_years:g}+ years experience" if job_min_years else "Experience alignment",
                                     status=status, explanation=explanation)
    return {"score": round(score * 100, 1), "finding": finding, "relevance": relevance}


def _education_scoring(cv_text: str, job_education_text: str | None) -> dict:
    if not job_education_text:
        return {"score": 100.0, "finding": None}
    required_level = extract_education_level(job_education_text)
    if not required_level:
        return {"score": 100.0, "finding": None}
    cv_level = extract_education_level(cv_text)
    cv_rank, req_rank = education_rank(cv_level), education_rank(required_level)

    if cv_rank >= req_rank:
        status, score = "met", 100.0
        explanation = f"Job requests {required_level}-level education or higher; your CV indicates a {cv_level or 'comparable'} degree."
    elif cv_rank == 0:
        status, score = "not_demonstrated", 30.0
        explanation = f"Job requests {required_level}-level education; no degree could be clearly identified in your CV. This does not necessarily mean you lack the required education - only that it wasn't detected in the extracted text."
    else:
        status, score = "partial", 60.0
        explanation = f"Job requests {required_level}-level education; your CV indicates a {cv_level} degree, which is below the stated requirement but may still be considered depending on the employer."

    finding = QualificationFinding(label=f"{required_level.title()}'s degree or higher", status=status, explanation=explanation)
    return {"score": score, "finding": finding}


def _responsibility_scoring(cv_text: str, responsibilities: str) -> dict:
    if not responsibilities:
        return {"score": 100.0, "alignment": []}
    sim = similarity(cv_text, responsibilities)
    # Surface which responsibility lines have some lexical overlap with the
    # CV, as a lightweight "alignment" list (spec section 19/32).
    resp_lines = [line.strip() for line in responsibilities.split(".") if line.strip()]
    cv_words = set(cv_text.lower().split())
    alignment = []
    for line in resp_lines:
        line_words = set(w.strip(",.") for w in line.lower().split() if len(w) > 4)
        overlap = line_words & cv_words
        if len(overlap) >= 2:
            alignment.append(line)
    return {"score": round(sim * 100, 1), "alignment": alignment}


def _structure_scoring(structure_notes: list[str]) -> dict:
    # Starts at 100, deducts per observed issue - capped, never claims a
    # formatting guarantee (spec section 48).
    score = max(40.0, 100.0 - 20.0 * len(structure_notes))
    return {"score": score, "notes": structure_notes}


def calculate_match(resume, job, required_skills: list[str], preferred_skills: list[str]) -> dict:
    """
    resume: app.models.resume.Resume (with parsed_text/parsed_data populated)
    job: app.models.job.Job
    Returns the full deterministic scoring + structured findings breakdown.
    """
    weights = settings.MATCH_WEIGHTS
    cv_text = resume.parsed_text or ""
    parsed = resume.parsed_data or {}
    cv_skills = (parsed.get("technical_skills") or []) + (parsed.get("soft_skills") or [])
    cv_years = parsed.get("years_experience")

    job_full_text = " ".join(filter(None, [job.description, job.requirements, job.responsibilities]))

    skills = _skills_scoring(cv_text, cv_skills, required_skills, preferred_skills)
    keywords = _keyword_scoring(cv_text, job_full_text, cv_skills)
    experience = _experience_scoring(cv_text, cv_years, _infer_min_years(job.requirements), job.responsibilities or "")
    education = _education_scoring(cv_text, job.requirements)
    responsibilities = _responsibility_scoring(cv_text, job.responsibilities or "")
    structure = _structure_scoring(parsed.get("structure_notes") or [])
    semantic = similarity(cv_text, job_full_text)

    overall = (
        weights["technical_skills"] * skills["score"]
        + weights["keywords"] * keywords["score"]
        + weights["experience"] * experience["score"]
        + weights["responsibilities"] * responsibilities["score"]
        + weights["education"] * education["score"]
        + weights["ats_structure"] * structure["score"]
    )

    keyword_findings = list(skills["findings"])
    experience_findings = [experience["finding"]]
    education_findings = [education["finding"]] if education["finding"] else []

    return {
        "overall_score": round(overall, 1),
        "skills_score": skills["score"],
        "keyword_score": keywords["score"],
        "experience_score": experience["score"],
        "education_score": education["score"],
        "responsibility_score": responsibilities["score"],
        "structure_score": structure["score"],
        "semantic_score": round(semantic * 100, 1),
        "keyword_findings": keyword_findings,
        "experience_findings": experience_findings,
        "education_findings": education_findings,
        "responsibility_alignment": responsibilities["alignment"],
        "structure_notes": structure["notes"],
        "weights_used": weights,
    }


def _infer_min_years(requirements_text: str | None) -> float | None:
    from app.ai.skill_taxonomy import extract_years_experience
    return extract_years_experience(requirements_text or "")
