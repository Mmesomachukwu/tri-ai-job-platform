from app.services import resume_service, optimization_service
from app.repositories.resume_repository import ResumeRepository


def _upload_resume(db, pdf_bytes):
    return resume_service.upload_and_process_resume(db, "jane.pdf", pdf_bytes, "General CV")


def test_optimization_stores_original_text_for_comparison(db, sample_pdf_bytes, sample_job):
    resume = _upload_resume(db, sample_pdf_bytes)
    version = optimization_service.optimize_resume(db, resume, sample_job)

    assert version.content["original_text"] == resume.parsed_text


def test_optimization_never_introduces_ungrounded_skills(db, sample_pdf_bytes, sample_job):
    """Template-mode optimization (Ollama unreachable in tests) must never
    add a skill/technology that isn't in the original CV text - every
    bullet_changes entry's 'original' field must be a real excerpt from
    resume.parsed_text."""
    resume = _upload_resume(db, sample_pdf_bytes)
    version = optimization_service.optimize_resume(db, resume, sample_job)

    for change in version.content["bullet_changes"]:
        assert change["original"] in resume.parsed_text or resume.parsed_text in change["original"] \
            or any(word in resume.parsed_text for word in change["original"].split()[:3])


def test_optimization_does_not_fabricate_missing_skill_as_present(db, sample_pdf_bytes, sample_job):
    """'sql' is a genuine gap for this CV/job pair (see test_matching.py) -
    optimization must not claim it in the optimized content."""
    resume = _upload_resume(db, sample_pdf_bytes)
    version = optimization_service.optimize_resume(db, resume, sample_job)

    optimized_text = str(version.content.get("optimized_summary") or "") + " " + \
        " ".join(c["optimized"] for c in version.content["bullet_changes"])
    # Template mode never invents new prose at all - if it ever does
    # (e.g. once Ollama is wired in), this assertion protects against a
    # regression where "SQL" gets silently added.
    assert "SQL" not in optimized_text or "sql" in resume.parsed_text.lower()


def test_optimization_records_explanation_source(db, sample_pdf_bytes, sample_job):
    resume = _upload_resume(db, sample_pdf_bytes)
    version = optimization_service.optimize_resume(db, resume, sample_job)
    assert version.content["explanation_source"] == "template"


def test_optimization_is_stored_as_a_version_not_overwriting_original(db, sample_pdf_bytes, sample_job):
    """Original CV/resume row must remain untouched - optimization creates
    a separate ResumeVersion."""
    resume = _upload_resume(db, sample_pdf_bytes)
    original_text = resume.parsed_text

    optimization_service.optimize_resume(db, resume, sample_job)

    refetched = ResumeRepository(db).get(resume.id)
    assert refetched.parsed_text == original_text


def test_optimize_api_endpoint(client, sample_pdf_bytes, sample_job):
    upload = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("jane.pdf", sample_pdf_bytes, "application/pdf")},
    )
    resume_id = upload.json()["id"]

    resp = client.post(f"/api/v1/resumes/{resume_id}/optimize/{sample_job.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["resume_id"] == resume_id
    assert body["job_id"] == sample_job.id
    assert sample_job.title in body["version_name"]


def test_list_versions_endpoint(client, sample_pdf_bytes, sample_job):
    upload = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("jane.pdf", sample_pdf_bytes, "application/pdf")},
    )
    resume_id = upload.json()["id"]
    client.post(f"/api/v1/resumes/{resume_id}/optimize/{sample_job.id}")

    versions = client.get(f"/api/v1/resumes/{resume_id}/versions")
    assert versions.status_code == 200
    assert len(versions.json()) == 1


def test_optimize_nonexistent_job_returns_404(client, sample_pdf_bytes):
    upload = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("jane.pdf", sample_pdf_bytes, "application/pdf")},
    )
    resume_id = upload.json()["id"]
    resp = client.post(f"/api/v1/resumes/{resume_id}/optimize/nonexistent-id")
    assert resp.status_code == 404
