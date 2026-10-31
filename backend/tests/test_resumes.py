def test_upload_valid_pdf(client, sample_pdf_bytes):
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("jane.pdf", sample_pdf_bytes, "application/pdf")},
        data={"label": "General CV"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction_status"] == "success"
    assert body["parsed_data"]["contact"]["email"] == "jane@example.com"
    assert "python" in body["parsed_data"]["technical_skills"]


def test_upload_valid_docx(client, sample_docx_bytes):
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("john.docx", sample_docx_bytes,
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction_status"] == "success"
    assert "python" in body["parsed_data"]["technical_skills"]
    assert "kubernetes" in body["parsed_data"]["technical_skills"]


def test_upload_rejects_unsupported_file_type(client):
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", b"just plain text", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_upload_rejects_oversized_file(client):
    huge = b"%PDF-1.4\n" + (b"0" * (6 * 1024 * 1024))  # over the 5MB limit
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("big.pdf", huge, "application/pdf")},
    )
    assert resp.status_code == 400
    assert "size limit" in resp.json()["detail"]


def test_upload_handles_corrupt_pdf_gracefully(client):
    """A .pdf extension with garbage bytes should fail extraction cleanly
    (extraction_status='failed' with an explanation), not crash the API."""
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("corrupt.pdf", b"not actually a pdf file", "application/pdf")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction_status"] == "failed"
    assert body["extraction_error"] is not None


def test_list_and_get_and_delete_resume(client, sample_pdf_bytes):
    upload = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("jane.pdf", sample_pdf_bytes, "application/pdf")},
    )
    resume_id = upload.json()["id"]

    listing = client.get("/api/v1/resumes")
    assert len(listing.json()) == 1

    single = client.get(f"/api/v1/resumes/{resume_id}")
    assert single.status_code == 200

    deleted = client.delete(f"/api/v1/resumes/{resume_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/resumes/{resume_id}").status_code == 404


def test_get_nonexistent_resume(client):
    resp = client.get("/api/v1/resumes/nonexistent-id")
    assert resp.status_code == 404


def test_path_traversal_filename_rejected_safely(client, sample_pdf_bytes):
    """Regression test for the path-traversal fix in resume_service.save_file():
    a malicious filename must not escape LOCAL_STORAGE_DIR."""
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("../../../../etc/passwd.pdf", sample_pdf_bytes, "application/pdf")},
    )
    # Should either succeed with a sanitized filename or fail cleanly -
    # never write outside the storage directory.
    assert resp.status_code in (200, 400)
    if resp.status_code == 200:
        from app.database.config import settings
        import os
        resume_id = resp.json()["id"]
        from app.database.session import SessionLocal
        from app.repositories.resume_repository import ResumeRepository
        db = SessionLocal()
        resume = ResumeRepository(db).get(resume_id)
        stored_path = os.path.realpath(resume.file_path)
        storage_dir = os.path.realpath(str(settings.LOCAL_STORAGE_DIR))
        assert stored_path.startswith(storage_dir)
        db.close()
