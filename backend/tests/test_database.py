from app.database.session import check_db_connection
from app.repositories.resume_repository import ResumeRepository
from app.repositories.job_repository import JobRepository


def test_db_connection_ok():
    ok, error = check_db_connection()
    assert ok is True
    assert error is None


def test_resume_crud(db):
    repo = ResumeRepository(db)
    resume = repo.create(filename="test.pdf", file_path="/tmp/test.pdf", extraction_status="pending")
    assert resume.id is not None

    fetched = repo.get(resume.id)
    assert fetched.filename == "test.pdf"

    updated = repo.update(resume, extraction_status="success")
    assert updated.extraction_status == "success"

    repo.delete(resume)
    assert repo.get(resume.id) is None


def test_resume_version_fk_enforced(db):
    """A resume_version referencing a nonexistent resume should fail -
    verifies FK constraints are actually enforced by the schema."""
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.repositories.resume_repository import ResumeRepository

    repo = ResumeRepository(db)
    with pytest.raises(IntegrityError):
        repo.create_version(
            resume_id="00000000-0000-0000-0000-000000000000",
            version_name="x", content={},
        )
    db.rollback()


def test_dedup_hash_prevents_duplicate_jobs(db, sample_job):
    """Same title+company+location should be treated as the same job on
    re-sync (dedup_hash lookup), not duplicated."""
    repo = JobRepository(db)
    existing = repo.get_by_dedup_hash(sample_job.dedup_hash)
    assert existing is not None
    assert existing.id == sample_job.id
