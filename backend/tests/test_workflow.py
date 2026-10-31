"""
Full product workflow, exercised through the real HTTP API exactly as a
frontend would call it:

Search job -> select job -> upload CV -> analyze -> score ->
keyword/responsibility gaps -> optimize CV -> save job
"""
from unittest.mock import patch


def test_complete_workflow(client, sample_pdf_bytes):
    # 1. Seed real-looking jobs into the DB the way sync_jobs would (via a
    #    mocked RealJobProvider response - no MockJobProvider in the app).
    fake_jobs = [{
        "external_id": "wf-1", "source": "remoteok_public_api",
        "title": "Backend Software Engineer", "company": "WorkflowCo",
        "location": "Remote", "remote_type": "Remote", "employment_type": "Full-time",
        "description": "Build scalable backend APIs.",
        "requirements": "2+ years backend development. Bachelor's degree in Computer Science required. Strong SQL skills.",
        "responsibilities": "Build scalable backend APIs. Design and maintain PostgreSQL schemas. Write automated tests.",
        "required_skills": ["python", "sql", "rest api", "postgresql"],
        "preferred_skills": ["docker"],
        "job_url": "https://example.com/wf-1", "posted_date": "2026-09-01T00:00:00",
    }]
    with patch("app.jobs.real_provider.RealJobProvider.search_jobs", return_value=fake_jobs):
        sync_resp = client.post("/api/v1/jobs/sync")
    assert sync_resp.status_code == 200

    # 2. Search real jobs
    search_resp = client.get("/api/v1/jobs", params={"keyword": "Backend"})
    assert search_resp.status_code == 200
    results = search_resp.json()["results"]
    assert len(results) == 1
    job_id = results[0]["id"]
    assert results[0]["job_url"] == "https://example.com/wf-1"  # original URL preserved

    # 3. Select job -> view details
    detail_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["title"] == "Backend Software Engineer"

    # 4. Upload CV
    upload_resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("jane.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert upload_resp.status_code == 200
    resume_id = upload_resp.json()["id"]
    assert upload_resp.json()["extraction_status"] == "success"

    # 5. Analyze CV against the specific selected job
    analyze_resp = client.post(f"/api/v1/analyses/resumes/{resume_id}/jobs/{job_id}")
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()

    # 6. Match score present and explainable
    assert 0 <= analysis["overall_score"] <= 100
    for component in ["skills_score", "keyword_score", "experience_score",
                       "education_score", "responsibility_score", "structure_score"]:
        assert 0 <= analysis[component] <= 100

    # 7. Keyword/gap findings present, using correct grounding language
    findings = analysis["analysis_result"]["keyword_findings"]
    demonstrated = [f for f in findings if f["status"] == "demonstrated"]
    gaps = [f for f in findings if f["status"] == "gap"]
    assert len(demonstrated) > 0
    assert len(gaps) > 0
    assert all(f["cv_evidence"] is not None for f in demonstrated)
    assert all(f["cv_evidence"] is None for f in gaps)

    # 8. Recommendations grounded in this specific job's gaps
    assert len(analysis["recommendations"]) > 0
    combined = " ".join(analysis["recommendations"]).lower()
    assert "you don't have" not in combined

    # 9. Optimize CV for this job
    optimize_resp = client.post(f"/api/v1/resumes/{resume_id}/optimize/{job_id}")
    assert optimize_resp.status_code == 200
    version = optimize_resp.json()
    assert version["job_id"] == job_id

    # 10. Original vs optimized comparison available
    assert "original_text" in version["content"]
    assert version["content"]["original_text"] is not None

    # 11. Save the job
    save_resp = client.post(f"/api/v1/saved-jobs/{job_id}")
    assert save_resp.status_code == 200
    assert save_resp.json()["status"] == "saved"

    saved_list = client.get("/api/v1/saved-jobs")
    assert len(saved_list.json()) == 1
    assert saved_list.json()[0]["id"] == job_id

    # 12. No auth was required at any step (single-tenant app)
    # (implicit - no Authorization header was ever sent above)


def test_workflow_gracefully_handles_real_provider_outage(client):
    """If the real provider is down mid-workflow, the user gets a clear
    error, never fake jobs silently appearing."""
    with patch("app.jobs.real_provider.RealJobProvider.search_jobs", return_value=[]):
        resp = client.post("/api/v1/jobs/sync")
    assert resp.status_code == 503
    assert "Unable to retrieve real jobs" in resp.json()["detail"]

    # And the job list is correctly empty, not populated with anything fake
    listing = client.get("/api/v1/jobs")
    assert listing.json()["total"] == 0
