import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Index
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    external_id = Column(String, nullable=True, index=True)
    source = Column(String, nullable=False)  # mock | remoteok_public_api | remotive_public_api | greenhouse | lever

    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)  # Data Science & AI | Software Engineering | etc.

    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    responsibilities = Column(Text, nullable=True)

    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    employment_type = Column(String, nullable=True, index=True)  # Full-time | Part-time | Contract | Internship
    remote_type = Column(String, nullable=True, index=True)      # Remote | Hybrid | On-site
    experience_level = Column(String, nullable=True, index=True)  # Entry | Junior | Mid-level | Senior | Lead

    posted_date = Column(DateTime, nullable=True)
    job_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    dedup_hash = Column(String, index=True, nullable=False)

    __table_args__ = (Index("ix_jobs_source_external_id", "source", "external_id"),)


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill = Column(String, nullable=False, index=True)
    is_required = Column(String, default="true")  # "true" = required, "false" = preferred


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
