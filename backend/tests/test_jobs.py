"""
Job search/filter/details/saved-jobs tests. Job data is seeded directly
via the repository (seed_mock_jobs fixture) rather than through a
provider - the app has no MockJobProvider (removed per spec section 5),
so these tests exercise search/filter logic against known data instead of
depending on network access to real job APIs.
"""


def test_job_search_returns_seeded_jobs(client, seed_mock_jobs):
    resp = client.get("/api/v1/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4


def test_job_search_keyword(client, seed_mock_jobs):
    resp = client.get("/api/v1/jobs", params={"keyword": "engineer"})
    body = resp.json()
    assert body["total"] > 0
    for j in body["results"]:
        haystack = f"{j['title']} {j['company']} {j['description']}".lower()
        assert "engineer" in haystack


def test_job_search_category_filter(client, seed_mock_jobs):
    resp = client.get("/api/v1/jobs", params={"category": "Data Science & AI"})
    body = resp.json()
    assert body["total"] == 3  # ML Engineer, Data Engineer, Data Scientist
    for j in body["results"]:
        assert j["category"] == "Data Science & AI"


def test_job_search_remote_type_filter(client, seed_mock_jobs):
    resp = client.get("/api/v1/jobs", params={"remote_type": "Remote"})
    body = resp.json()
    assert body["total"] >= 1
    assert all(j["remote_type"] == "Remote" for j in body["results"])


def test_job_search_skills_filter(client, seed_mock_jobs):
    resp = client.get("/api/v1/jobs", params={"skills": "aws"})
    body = resp.json()
    assert body["total"] == 1
    assert "aws" in body["results"][0]["required_skills"] + body["results"][0]["preferred_skills"]


def test_job_pagination(client, seed_mock_jobs):
    resp = client.get("/api/v1/jobs", params={"page": 1, "page_size": 2})
    body = resp.json()
    assert len(body["results"]) == 2
    assert body["page"] == 1


def test_job_details(client, sample_job):
    resp = client.get(f"/api/v1/jobs/{sample_job.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Backend Software Engineer"
    assert "python" in body["required_skills"]


def test_job_details_not_found(client):
    resp = client.get("/api/v1/jobs/nonexistent-id")
    assert resp.status_code == 404


def test_save_and_unsave_job(client, sample_job):
    save = client.post(f"/api/v1/saved-jobs/{sample_job.id}")
    assert save.status_code == 200
    assert save.json()["status"] == "saved"

    listing = client.get("/api/v1/saved-jobs")
    assert len(listing.json()) == 1

    save_again = client.post(f"/api/v1/saved-jobs/{sample_job.id}")
    assert save_again.json()["status"] == "already_saved"

    unsave = client.delete(f"/api/v1/saved-jobs/{sample_job.id}")
    assert unsave.json()["status"] == "removed"
    listing2 = client.get("/api/v1/saved-jobs")
    assert len(listing2.json()) == 0


def test_save_nonexistent_job_fails(client):
    resp = client.post("/api/v1/saved-jobs/nonexistent-id")
    assert resp.status_code == 404


def test_is_saved_flag_reflected_in_search(client, sample_job):
    client.post(f"/api/v1/saved-jobs/{sample_job.id}")
    resp = client.get(f"/api/v1/jobs/{sample_job.id}")
    assert resp.json()["is_saved"] is True


def test_no_auth_required_anywhere(client, sample_job):
    """Single-tenant app - every route should work with zero auth headers."""
    assert client.get("/api/v1/jobs").status_code == 200
    assert client.get(f"/api/v1/jobs/{sample_job.id}").status_code == 200
    assert client.get("/api/v1/saved-jobs").status_code == 200
    assert client.get("/api/v1/resumes").status_code == 200
