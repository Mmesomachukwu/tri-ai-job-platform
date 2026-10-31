from app.services import resume_service, analysis_service
from app.ai.factory import get_ai_service


def _upload_resume(db, pdf_bytes):
    return resume_service.upload_and_process_resume(db, "jane.pdf", pdf_bytes, "General CV")


def test_ollama_unavailable_falls_back_to_template(db, sample_pdf_bytes, sample_job):
    """OLLAMA_BASE_URL is deliberately unreachable in the test environment
    (see conftest.py) - this confirms the app detects that and uses the
    template fallback rather than erroring or hanging."""
    service, source = get_ai_service()
    assert source == "template"
    assert service.is_available() is True  # template fallback is always available


def test_analysis_records_explanation_source(db, sample_pdf_bytes, sample_job):
    resume = _upload_resume(db, sample_pdf_bytes)
    analysis = analysis_service.run_analysis(db, resume, sample_job)
    assert analysis.explanation_source == "template"


def test_analysis_never_lets_ai_failure_propagate_as_error(db, sample_pdf_bytes, sample_job):
    """Even with Ollama completely unreachable, POST /analyses/... must
    still return a valid analysis (spec section 44/25) - never a 500 and
    never a fabricated 'AI analysis unavailable' with no data."""
    resume = _upload_resume(db, sample_pdf_bytes)
    analysis = analysis_service.run_analysis(db, resume, sample_job)
    assert analysis.overall_score is not None
    assert analysis.recommendations is not None
    assert len(analysis.recommendations) > 0


def test_recommendations_are_grounded_in_job_specific_gaps(db, sample_pdf_bytes, sample_job):
    """Recommendations must reference the SPECIFIC job's missing
    requirements (e.g. 'sql'), not generic resume advice."""
    resume = _upload_resume(db, sample_pdf_bytes)
    analysis = analysis_service.run_analysis(db, resume, sample_job)

    combined = " ".join(analysis.recommendations).lower()
    assert "sql" in combined  # the actual gap for this CV/job pair


def test_recommendations_never_claim_absence_of_skill(db, sample_pdf_bytes, sample_job):
    """Must say 'not currently demonstrated', never 'you don't have this
    skill' - the app cannot know what the candidate actually possesses,
    only what the CV text shows."""
    resume = _upload_resume(db, sample_pdf_bytes)
    analysis = analysis_service.run_analysis(db, resume, sample_job)

    combined = " ".join(analysis.recommendations).lower()
    assert "you don't have" not in combined
    assert "you do not have" not in combined


def test_keyword_findings_in_analysis_result_use_gap_not_absence_language(db, sample_pdf_bytes, sample_job):
    resume = _upload_resume(db, sample_pdf_bytes)
    analysis = analysis_service.run_analysis(db, resume, sample_job)

    gap_findings = [f for f in analysis.analysis_result["keyword_findings"] if f["status"] == "gap"]
    assert len(gap_findings) > 0
    for f in gap_findings:
        assert f["cv_evidence"] is None


def test_analysis_api_endpoint_full_flow(client, sample_pdf_bytes, sample_job):
    upload = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("jane.pdf", sample_pdf_bytes, "application/pdf")},
    )
    resume_id = upload.json()["id"]

    analyze = client.post(f"/api/v1/analyses/resumes/{resume_id}/jobs/{sample_job.id}")
    assert analyze.status_code == 200
    body = analyze.json()
    assert 0 <= body["overall_score"] <= 100
    assert body["explanation_source"] == "template"

    fetched = client.get(f"/api/v1/analyses/resumes/{resume_id}/jobs/{sample_job.id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_analyze_nonexistent_job_returns_404(client, sample_pdf_bytes):
    upload = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("jane.pdf", sample_pdf_bytes, "application/pdf")},
    )
    resume_id = upload.json()["id"]
    resp = client.post(f"/api/v1/analyses/resumes/{resume_id}/jobs/nonexistent-id")
    assert resp.status_code == 404


def test_analyze_nonexistent_resume_returns_404(client, sample_job):
    resp = client.post(f"/api/v1/analyses/resumes/nonexistent-id/jobs/{sample_job.id}")
    assert resp.status_code == 404


def test_analyze_failed_resume_returns_400(client, sample_job):
    upload = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("corrupt.pdf", b"not a real pdf", "application/pdf")},
    )
    resume_id = upload.json()["id"]
    resp = client.post(f"/api/v1/analyses/resumes/{resume_id}/jobs/{sample_job.id}")
    assert resp.status_code == 400
