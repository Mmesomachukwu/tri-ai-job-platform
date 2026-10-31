from datetime import datetime
from typing import Literal
from pydantic import BaseModel, field_validator


class KeywordFinding(BaseModel):
    """
    One keyword/phrase finding from comparing a job's requirements against
    a CV. This shape is the factual-grounding rule made structural rather
    than just a prompt instruction:

    - "gap"          -> cv_evidence and suggestion MUST be None. A gap can
                         never carry text implying the CV already shows it.
    - "demonstrated"  -> cv_evidence MUST be set (the exact/near-exact CV
                         phrase that demonstrates the term).
    - "strengthen"    -> cv_evidence MUST be set (what's already there) AND
                         suggestion MUST be set (the proposed rewording).
                         A suggestion is only valid if it's a rewording of
                         cv_evidence, never new claims.
    """
    term: str
    status: Literal["demonstrated", "strengthen", "gap"]
    cv_evidence: str | None = None
    suggestion: str | None = None

    @field_validator("cv_evidence")
    @classmethod
    def gap_has_no_evidence(cls, v, info):
        if info.data.get("status") == "gap" and v is not None:
            raise ValueError("A 'gap' finding must not carry cv_evidence - nothing in the CV supports it.")
        if info.data.get("status") in ("demonstrated", "strengthen") and not v:
            raise ValueError(f"A '{info.data.get('status')}' finding requires cv_evidence.")
        return v

    @field_validator("suggestion")
    @classmethod
    def only_strengthen_has_suggestion(cls, v, info):
        if info.data.get("status") != "strengthen" and v is not None:
            raise ValueError("Only 'strengthen' findings may carry a suggestion.")
        if info.data.get("status") == "strengthen" and not v:
            raise ValueError("A 'strengthen' finding requires a suggestion.")
        return v


class QualificationFinding(BaseModel):
    label: str  # e.g. "3+ years Python development"
    status: Literal["met", "partial", "not_demonstrated"]
    explanation: str  # non-judgmental, e.g. "Job requests 3+ years; CV demonstrates ~2 years."


class AnalysisResult(BaseModel):
    """The full structured `analysis_result` JSON stored on the Analysis row."""
    keyword_findings: list[KeywordFinding]
    experience_findings: list[QualificationFinding]
    education_findings: list[QualificationFinding]
    responsibility_alignment: list[str]  # CV phrases that align with job responsibilities
    structure_notes: list[str]           # ATS-readability observations (no formatting guarantees)


class AnalysisOut(BaseModel):
    id: str
    resume_id: str
    job_id: str
    overall_score: float
    skills_score: float
    keyword_score: float
    experience_score: float
    education_score: float
    responsibility_score: float
    structure_score: float
    semantic_score: float
    analysis_result: dict
    recommendations: list[str]
    explanation_source: str
    created_at: datetime

    class Config:
        from_attributes = True
