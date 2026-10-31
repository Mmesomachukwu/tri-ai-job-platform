"""
AI service abstraction (spec section 9-10). The rest of the app talks only
to this interface, never directly to Ollama - so the provider can be
swapped later without touching callers.

Every method here produces EXPLANATORY TEXT ONLY. None of them return or
influence the numeric score - that's calculated exclusively by
app/services/matching_service.py. This split is enforced by what each
method's return type contains, not just by convention.
"""
from abc import ABC, abstractmethod


class AIService(ABC):
    @abstractmethod
    def analyze_resume(self, resume_text: str, job_context: dict, match_result: dict) -> dict:
        """Returns {"summary": str, "recommendations": list[str],
        "keyword_suggestions": dict[str, str]} - prose explaining an
        already-computed match_result. Must not alter any score."""
        raise NotImplementedError

    @abstractmethod
    def optimize_resume(self, resume_text: str, parsed_data: dict, job_context: dict, match_result: dict) -> dict:
        """Returns an optimized version of resume content, using ONLY
        facts already present in resume_text/parsed_data. See
        app/services/optimization_service.py for the factual-grounding
        enforcement built on top of this."""
        raise NotImplementedError

    @abstractmethod
    def extract_job_requirements(self, job_description: str) -> dict:
        """Returns structured requirements extracted from a free-text job
        description, to supplement the DB's already-structured fields."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError
