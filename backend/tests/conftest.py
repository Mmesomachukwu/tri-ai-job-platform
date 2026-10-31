"""
Test fixtures. Single-tenant app - no auth, no users. Tests run against a
REAL PostgreSQL database (TEST_DATABASE_URL, defaults to job_ai_test), not
SQLite or mocks, since PostgreSQL-specific behavior (constraints, JSON
columns) needs to actually be exercised.

Since MockJobProvider was removed from the application entirely (per
spec section 5), tests that need job data seed it directly via
JobRepository (bypassing any provider), and RealJobProvider's HTTP
behavior is tested separately with mocked network responses
(test_job_provider.py) rather than via a live network call.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/job_ai_test"
)
os.environ["AI_PROVIDER"] = "ollama"  # intentionally: tests verify the fallback engages
os.environ["OLLAMA_BASE_URL"] = "http://localhost:19999"  # deliberately unreachable in test env

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base, get_db
from app.models import job, resume, analysis  # noqa: F401 - register models
from app.main import app

TEST_DB_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DB_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestSessionLocal()
    yield session
    session.close()
    with engine.connect() as conn:
        trans = conn.begin()
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        trans.commit()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_bytes():
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    text = """Jane Student
jane@example.com | linkedin.com/in/janestudent | github.com/janestudent

EDUCATION
Bachelor of Science in Computer Science, University of Toronto, 2026

EXPERIENCE
Software Engineering Intern, TechCo - 1 year
Developed REST APIs using Python and FastAPI. Worked with PostgreSQL databases.
Used Docker for containerization. Wrote unit tests.

SKILLS
Python, FastAPI, PostgreSQL, Docker, Git, JavaScript, React
"""
    page.insert_text((50, 50), text, fontsize=11)
    return doc.tobytes()


@pytest.fixture
def sample_docx_bytes():
    import docx
    import io
    document = docx.Document()
    document.add_paragraph("John Backend Dev")
    document.add_paragraph("john@example.com")
    document.add_paragraph("EXPERIENCE")
    document.add_paragraph("Backend Engineer, DataCo - 3 years")
    document.add_paragraph("Built REST APIs with Python, SQL, and Docker.")
    document.add_paragraph("SKILLS")
    document.add_paragraph("Python, SQL, Docker, Kubernetes, AWS")
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


@pytest.fixture
def sample_job(db):
    from app.repositories.job_repository import JobRepository
    from app.jobs.normalizer import normalize_job

    raw = {
        "external_id": "test-job-1",
        "title": "Backend Software Engineer",
        "company": "TestCo",
        "location": "Remote",
        "remote_type": "Remote",
        "employment_type": "Full-time",
        "experience_level": "Mid-level",
        "description": "Build scalable backend APIs.",
        "requirements": "2+ years backend development. Bachelor's degree in Computer Science required. Strong SQL skills.",
        "responsibilities": "Build scalable backend APIs. Design and maintain PostgreSQL schemas. Write automated tests.",
        "required_skills": ["python", "sql", "rest api", "postgresql"],
        "preferred_skills": ["docker", "kubernetes"],
        "job_url": "https://example.com/jobs/test-job-1",
        "posted_date": "2026-09-01T00:00:00",
    }
    normalized = normalize_job(raw, "test_source")
    required = normalized.pop("required_skills")
    preferred = normalized.pop("preferred_skills")
    repo = JobRepository(db)
    job_obj = repo.create(**normalized)
    repo.replace_skills(job_obj.id, required, preferred)
    return job_obj


@pytest.fixture
def seed_mock_jobs(db):
    """
    Seeds a small, deterministic set of jobs directly via the repository -
    the test equivalent of what a JobProvider would return, without the
    app itself containing a MockJobProvider (removed per spec section 5).
    """
    from app.repositories.job_repository import JobRepository
    from app.jobs.normalizer import normalize_job

    raw_jobs = [
        {
            "external_id": "seed-1", "title": "Machine Learning Engineer", "company": "Northwind AI",
            "location": "Toronto, ON", "remote_type": "Hybrid", "employment_type": "Full-time",
            "description": "Build ML models.", "requirements": "3+ years Python.",
            "responsibilities": "Develop predictive machine learning models.",
            "required_skills": ["python", "machine learning"], "preferred_skills": ["aws"],
            "job_url": "https://example.com/seed-1", "posted_date": "2026-09-10T00:00:00",
        },
        {
            "external_id": "seed-2", "title": "Data Engineer", "company": "Northwind AI",
            "location": "Remote", "remote_type": "Remote", "employment_type": "Full-time",
            "description": "Build data pipelines.", "requirements": "3+ years SQL.",
            "responsibilities": "Build and maintain ETL pipelines.",
            "required_skills": ["python", "sql", "etl"], "preferred_skills": ["airflow"],
            "job_url": "https://example.com/seed-2", "posted_date": "2026-09-09T00:00:00",
        },
        {
            "external_id": "seed-3", "title": "Data Scientist", "company": "Meridian Analytics",
            "location": "Vancouver, BC", "remote_type": "Hybrid", "employment_type": "Full-time",
            "description": "Analyze data.", "requirements": "Bachelor's degree required.",
            "responsibilities": "Analyze large datasets and develop predictive models.",
            "required_skills": ["python", "statistics"], "preferred_skills": ["r"],
            "job_url": "https://example.com/seed-3", "posted_date": "2026-09-05T00:00:00",
        },
        {
            "external_id": "seed-4", "title": "Frontend Software Engineer", "company": "Fernhill Software",
            "location": "Toronto, ON", "remote_type": "Hybrid", "employment_type": "Full-time",
            "description": "Build UIs.", "requirements": "1+ years React.",
            "responsibilities": "Implement UI components.",
            "required_skills": ["javascript", "react"], "preferred_skills": ["typescript"],
            "job_url": "https://example.com/seed-4", "posted_date": "2026-09-14T00:00:00",
        },
    ]
    repo = JobRepository(db)
    created = []
    for raw in raw_jobs:
        normalized = normalize_job(raw, "test_source")
        required = normalized.pop("required_skills")
        preferred = normalized.pop("preferred_skills")
        job_obj = repo.create(**normalized)
        repo.replace_skills(job_obj.id, required, preferred)
        created.append(job_obj)
    return created
