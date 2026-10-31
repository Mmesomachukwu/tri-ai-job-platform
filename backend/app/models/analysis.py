import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Float, ForeignKey
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class Analysis(Base):
    """
    One CV-vs-job analysis. `overall_score` and every `*_score` field are
    always produced by the deterministic scoring engine
    (app/services/matching_service.py) - never by the LLM. `analysis_result`
    holds the structured keyword/skill findings (see
    app/schemas/analysis.py:KeywordFinding) and `recommendations` holds the
    AI-generated (or template-generated, if Ollama is unavailable)
    explanatory text - prose only, no numbers originate there.
    """
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=gen_uuid)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    overall_score = Column(Float, nullable=False)
    skills_score = Column(Float, nullable=False)
    keyword_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    responsibility_score = Column(Float, nullable=False)
    structure_score = Column(Float, nullable=False)
    semantic_score = Column(Float, nullable=False)

    analysis_result = Column(JSON, nullable=False)   # keyword findings, skill matches/gaps, structured detail
    recommendations = Column(JSON, nullable=False)   # list of recommendation strings
    explanation_source = Column(String, default="template")  # "template" | "ollama"

    created_at = Column(DateTime, default=datetime.utcnow)
