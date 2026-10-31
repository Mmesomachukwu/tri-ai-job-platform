import json
from unittest.mock import patch
from app.jobs.real_provider import RealJobProvider
from app.jobs.normalizer import normalize_job, classify_category
from app.services import job_service


class _FakeResp:
    def __init__(self, data):
        self.data = json.dumps(data).encode() if not isinstance(data, bytes) else data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_real_provider_parses_remoteok_response():
    sample = [
        {"legal": "notice"},  # RemoteOK's first element is metadata, not a job
        {"id": 123, "position": "Backend Engineer", "company": "RemoteCo",
         "location": "Worldwide", "tags": ["python", "django"],
         "description": "Build APIs.", "url": "https://remoteok.com/remote-jobs/123",
         "date": "2026-09-01T00:00:00"},
    ]
    with patch("urllib.request.urlopen", return_value=_FakeResp(sample)):
        provider = RealJobProvider()
        jobs = provider._fetch_remoteok()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Engineer"
    assert jobs[0]["job_url"] == "https://remoteok.com/remote-jobs/123"
    assert "python" in jobs[0]["required_skills"]


def test_real_provider_parses_remotive_response():
    sample = {"jobs": [
        {"id": 999, "title": "Data Scientist", "company_name": "DataCo",
         "candidate_required_location": "Worldwide", "tags": ["python", "ml"],
         "job_type": "full_time", "description": "Analyze data.",
         "url": "https://remotive.com/remote-jobs/data/data-scientist-999",
         "publication_date": "2026-09-05T00:00:00"},
    ]}
    with patch("urllib.request.urlopen", return_value=_FakeResp(sample)):
        provider = RealJobProvider()
        jobs = provider._fetch_remotive(query=None)
    assert len(jobs) == 1
    # Attribution requirement: must be Remotive's own URL, never rewritten.
    assert jobs[0]["job_url"] == "https://remotive.com/remote-jobs/data/data-scientist-999"


def test_real_provider_greenhouse_strips_html_description():
    sample = {"jobs": [
        {"id": 1, "title": "SRE", "location": {"name": "Remote"},
         "content": "<p>Join our <b>SRE</b> team.</p>",
         "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/1",
         "updated_at": "2026-09-01T00:00:00"},
    ]}
    with patch("urllib.request.urlopen", return_value=_FakeResp(sample)):
        provider = RealJobProvider(greenhouse_slugs=["acme"])
        jobs = provider._fetch_greenhouse()
    assert len(jobs) == 1
    assert "<p>" not in jobs[0]["description"]
    assert "SRE" in jobs[0]["description"]


def test_real_provider_fails_soft_on_network_error():
    """A network failure for one source must not raise - it should yield
    an empty list for that source so other sources/the caller can still
    proceed or correctly report unavailability."""
    with patch("urllib.request.urlopen", side_effect=OSError("network unreachable")):
        provider = RealJobProvider()
        jobs = provider._fetch_remoteok()
    assert jobs == []


def test_normalizer_classifies_category_from_title():
    assert classify_category("Machine Learning Engineer") == "Data Science & AI"
    assert classify_category("Backend Software Engineer") == "Software Engineering"
    assert classify_category("DevOps Engineer") == "Cloud & DevOps"
    assert classify_category("Cybersecurity Analyst") == "Cybersecurity"
    assert classify_category("Underwater Basket Weaver") == "Other Technology"


def test_normalizer_produces_stable_dedup_hash():
    raw = {"title": "Data Engineer", "company": "Acme", "location": "Remote", "job_url": "https://x.com/1"}
    a = normalize_job(raw, "test_source")
    b = normalize_job(raw, "test_source")
    assert a["dedup_hash"] == b["dedup_hash"]


def test_normalizer_handles_epoch_millis_date():
    raw = {"title": "X", "company": "Y", "job_url": "https://x.com/1", "posted_date": 1756000000000}
    normalized = normalize_job(raw, "test_source")
    assert normalized["posted_date"] is not None
    assert normalized["posted_date"].year == 2025


def test_sync_jobs_raises_clear_error_when_provider_unavailable(db):
    """Per spec section 5/37: if the real provider can't retrieve
    anything, sync_jobs must raise (never silently insert mock/fake
    jobs)."""
    import pytest
    with patch("app.jobs.real_provider.RealJobProvider.search_jobs", return_value=[]):
        with pytest.raises(job_service.JobProviderUnavailableError):
            job_service.sync_jobs(db)


def test_sync_endpoint_returns_503_not_fake_jobs(client):
    with patch("app.jobs.real_provider.RealJobProvider.search_jobs", return_value=[]):
        resp = client.post("/api/v1/jobs/sync")
    assert resp.status_code == 503
    assert "Unable to retrieve real jobs" in resp.json()["detail"]


def test_sync_jobs_inserts_normalized_real_jobs(db):
    fake_jobs = [{
        "external_id": "1", "source": "remoteok_public_api", "title": "Platform Engineer",
        "company": "RealCo", "location": "Remote", "remote_type": "Remote",
        "description": "Build platform tools.", "required_skills": ["kubernetes"],
        "job_url": "https://remoteok.com/remote-jobs/1", "posted_date": "2026-09-01T00:00:00",
    }]
    with patch("app.jobs.real_provider.RealJobProvider.search_jobs", return_value=fake_jobs):
        result = job_service.sync_jobs(db)
    assert result["created"] == 1

    total, jobs = job_service.search_jobs(db)
    assert total == 1
    assert jobs[0]["title"] == "Platform Engineer"
    assert jobs[0]["source"] == "remoteok_public_api"
