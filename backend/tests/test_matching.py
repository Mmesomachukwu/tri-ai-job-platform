from app.services import resume_service
from app.services.matching_service import calculate_match
from app.repositories.job_repository import JobRepository


def _upload_resume(db, pdf_bytes):
    return resume_service.upload_and_process_resume(db, "jane.pdf", pdf_bytes, "General CV")


def test_skills_match_finds_demonstrated_skills(db, sample_pdf_bytes, sample_job):
    resume = _upload_resume(db, sample_pdf_bytes)
    required, preferred = JobRepository(db).get_skills(sample_job.id)
    result = calculate_match(resume, sample_job, required, preferred)

    demonstrated = {f.term for f in result["keyword_findings"] if f.status == "demonstrated"}
    assert "python" in demonstrated
    assert "postgresql" in demonstrated
    assert "rest api" in demonstrated  # plural "REST APIs" in CV text must match singular skill term


def test_skills_match_identifies_gap_as_not_demonstrated(db, sample_pdf_bytes, sample_job):
    resume = _upload_resume(db, sample_pdf_bytes)
    required, preferred = JobRepository(db).get_skills(sample_job.id)
    result = calculate_match(resume, sample_job, required, preferred)

    gaps = {f.term for f in result["keyword_findings"] if f.status == "gap"}
    assert "sql" in gaps  # CV mentions "PostgreSQL databases" but never bare "SQL"

    gap_finding = next(f for f in result["keyword_findings"] if f.term == "sql")
    assert gap_finding.cv_evidence is None  # gap findings must never carry evidence
    assert gap_finding.suggestion is None


def test_keyword_finding_schema_rejects_fabricated_evidence():
    """A 'gap' finding is structurally forbidden from claiming CV
    evidence exists - this is the factual-grounding rule enforced at the
    schema level, not just a prompt instruction."""
    import pytest
    from pydantic import ValidationError
    from app.schemas.analysis import KeywordFinding

    with pytest.raises(ValidationError):
        KeywordFinding(term="aws", status="gap", cv_evidence="Used AWS extensively")


def test_demonstrated_finding_requires_evidence():
    import pytest
    from pydantic import ValidationError
    from app.schemas.analysis import KeywordFinding

    with pytest.raises(ValidationError):
        KeywordFinding(term="python", status="demonstrated", cv_evidence=None)


def test_strengthen_finding_requires_evidence_and_suggestion():
    import pytest
    from pydantic import ValidationError
    from app.schemas.analysis import KeywordFinding

    with pytest.raises(ValidationError):
        KeywordFinding(term="data analysis", status="strengthen", cv_evidence="Worked with data", suggestion=None)

    # Valid when both are present
    finding = KeywordFinding(
        term="data analysis", status="strengthen",
        cv_evidence="Worked with data", suggestion="Performed data analysis on...",
    )
    assert finding.status == "strengthen"


def test_experience_scoring_reflects_years_gap(db, sample_pdf_bytes, sample_job):
    """CV shows ~1 year, job wants 2+ years - experience_score should be
    meaningfully below 100, and the explanation should state both numbers
    factually rather than pass/fail language."""
    resume = _upload_resume(db, sample_pdf_bytes)
    required, preferred = JobRepository(db).get_skills(sample_job.id)
    result = calculate_match(resume, sample_job, required, preferred)

    assert result["experience_score"] < 100
    explanation = result["experience_findings"][0].explanation
    assert "1" in explanation and "2" in explanation


def test_education_scoring_meets_requirement(db, sample_pdf_bytes, sample_job):
    """CV has a Bachelor's degree, job requires one - should score 100
    and be marked 'met', not 'not_demonstrated'."""
    resume = _upload_resume(db, sample_pdf_bytes)
    required, preferred = JobRepository(db).get_skills(sample_job.id)
    result = calculate_match(resume, sample_job, required, preferred)

    assert result["education_score"] == 100.0
    assert result["education_findings"][0].status == "met"


def test_responsibility_alignment_detects_overlap(db, sample_pdf_bytes, sample_job):
    resume = _upload_resume(db, sample_pdf_bytes)
    required, preferred = JobRepository(db).get_skills(sample_job.id)
    result = calculate_match(resume, sample_job, required, preferred)

    assert result["responsibility_score"] > 0


def test_semantic_similarity_nonzero_for_related_text():
    from app.ai.embedding_service import similarity

    sim = similarity(
        "Developed classification models using Python and scikit-learn.",
        "Build predictive machine learning models.",
    )
    assert 0.0 < sim <= 1.0


def test_semantic_similarity_zero_for_empty_text():
    from app.ai.embedding_service import similarity
    assert similarity("", "some job description") == 0.0
    assert similarity("some cv text", "") == 0.0


def test_deterministic_score_reproducible(db, sample_pdf_bytes, sample_job):
    """Running the scoring engine twice on identical inputs must produce
    identical results - it must never involve randomness or an LLM call."""
    resume = _upload_resume(db, sample_pdf_bytes)
    required, preferred = JobRepository(db).get_skills(sample_job.id)

    result_a = calculate_match(resume, sample_job, required, preferred)
    result_b = calculate_match(resume, sample_job, required, preferred)

    assert result_a["overall_score"] == result_b["overall_score"]
    assert result_a["skills_score"] == result_b["skills_score"]
    assert result_a["keyword_score"] == result_b["keyword_score"]


def test_score_breakdown_contains_all_required_components(db, sample_pdf_bytes, sample_job):
    resume = _upload_resume(db, sample_pdf_bytes)
    required, preferred = JobRepository(db).get_skills(sample_job.id)
    result = calculate_match(resume, sample_job, required, preferred)

    for key in ["overall_score", "skills_score", "keyword_score", "experience_score",
                "education_score", "responsibility_score", "structure_score", "semantic_score"]:
        assert key in result
        assert 0 <= result[key] <= 100


def test_different_jobs_produce_different_scores_for_same_cv(db, sample_pdf_bytes, sample_job):
    """Spec requirement: the same CV should get a different score for a
    different job."""
    from app.jobs.normalizer import normalize_job
    from app.repositories.job_repository import JobRepository as JR

    resume = _upload_resume(db, sample_pdf_bytes)
    required, preferred = JR(db).get_skills(sample_job.id)
    result_backend = calculate_match(resume, sample_job, required, preferred)

    unrelated_raw = {
        "title": "Cybersecurity Analyst", "company": "SecureCo", "location": "Remote",
        "description": "Monitor security alerts.",
        "requirements": "5+ years SIEM experience. Master's degree preferred.",
        "responsibilities": "Investigate security incidents and perform penetration testing.",
        "required_skills": ["siem", "incident response", "penetration testing"],
        "preferred_skills": [],
        "job_url": "https://example.com/unrelated", "posted_date": "2026-09-01T00:00:00",
    }
    normalized = normalize_job(unrelated_raw, "test_source")
    req2 = normalized.pop("required_skills")
    pref2 = normalized.pop("preferred_skills")
    repo = JR(db)
    unrelated_job = repo.create(**normalized)
    repo.replace_skills(unrelated_job.id, req2, pref2)

    result_unrelated = calculate_match(resume, unrelated_job, req2, pref2)

    assert result_backend["overall_score"] != result_unrelated["overall_score"]
