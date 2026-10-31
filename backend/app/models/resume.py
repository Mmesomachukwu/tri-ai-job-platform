import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=gen_uuid)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    label = Column(String, nullable=True)  # e.g. "Data Science CV", "General CV"
    is_primary = Column(String, default="false")  # "true" for the CV used as default in matching

    parsed_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=True)  # structured: contact/education/experience/skills etc.
    extraction_status = Column(String, default="pending")  # pending | success | failed
    extraction_error = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResumeVersion(Base):
    """Snapshot of an optimized CV, tied to the job it was optimized for."""
    __tablename__ = "resume_versions"

    id = Column(String, primary_key=True, default=gen_uuid)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    version_name = Column(String, nullable=False)  # e.g. "Optimized for Data Scientist @ Acme"
    content = Column(JSON, nullable=False)  # structured optimized content + diff of changes
    created_at = Column(DateTime, default=datetime.utcnow)


class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    id = Column(String, primary_key=True, default=gen_uuid)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    skill = Column(String, nullable=False, index=True)
