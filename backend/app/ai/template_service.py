"""
Deterministic, rule-based fallback for AIService. Runs when Ollama is
unavailable (spec section 44 - "AI analysis is currently unavailable" is
NOT acceptable when a free local alternative can still produce a grounded,
honest explanation). Zero dependencies, always available, and - like
OllamaAIService - structurally incapable of fabricating facts, since it
only ever echoes back cv_evidence/terms already computed by
matching_service.py.
"""
from app.ai.ai_service import AIService


class TemplateAIService(AIService):
    def is_available(self) -> bool:
        return True

    def analyze_resume(self, resume_text: str, job_context: dict, match_result: dict) -> dict:
        score = match_result["overall_score"]
        title = job_context.get("title", "this role")
        matched = [f.term for f in match_result["keyword_findings"] if f.status == "demonstrated"]
        missing = [f.term for f in match_result["keyword_findings"] if f.status == "gap"]

        if score >= 80:
            tone = f"Your CV shows strong alignment with the {title} role."
        elif score >= 60:
            tone = f"Your CV shows reasonable alignment with the {title} role, with some gaps to address."
        elif score >= 40:
            tone = f"Your CV partially aligns with the {title} role, but several requirements are not demonstrated."
        else:
            tone = f"This {title} role appears to be a stretch fit based on what's currently in your CV."

        parts = [tone]
        if matched:
            parts.append(f"Skills clearly demonstrated: {', '.join(matched[:5])}.")
        if missing:
            parts.append(f"Not currently demonstrated in your CV: {', '.join(missing[:5])}.")
        summary = " ".join(parts)

        recommendations = []
        for term in missing[:5]:
            recommendations.append(
                f"'{term}' appears in this job's requirements but is not currently demonstrated in your CV. "
                f"If you have genuine experience with it, consider making it visible."
            )
        for finding in match_result.get("experience_findings", []):
            if finding.status != "met":
                recommendations.append(finding.explanation)
        for finding in match_result.get("education_findings", []):
            if finding and finding.status != "met":
                recommendations.append(finding.explanation)
        if match_result["responsibility_score"] < 60:
            recommendations.append(
                "Consider more directly connecting your past experience to this role's specific responsibilities in your bullet points."
            )
        if not recommendations:
            recommendations.append("Your CV is already well aligned with this role's stated requirements.")

        return {"summary": summary, "recommendations": recommendations}

    def optimize_resume(self, resume_text: str, parsed_data: dict, job_context: dict, match_result: dict) -> dict:
        """
        Without a generative model, 'optimization' is limited to
        surfacing which existing CV sentences are most relevant to this
        job (so the candidate can reorder/emphasize them) rather than
        generating new prose - this keeps the factual-grounding guarantee
        absolute even without an LLM in the loop.
        """
        demonstrated_terms = [f.term for f in match_result["keyword_findings"] if f.status == "demonstrated"]
        alignment = match_result.get("responsibility_alignment", [])

        bullet_changes = []
        for line in alignment[:5]:
            bullet_changes.append({
                "original": line,
                "optimized": line,  # no rewording without a generative model - see changes_explanation
            })

        changes_explanation = (
            "Local template mode (no generative model connected): this highlights which of your "
            "existing CV sentences most closely relate to this job's responsibilities, and which of "
            "your demonstrated skills to keep visible near the top. No wording was changed - connect "
            "Ollama for AI-rewritten phrasing, still constrained to facts already in your CV."
        )
        if demonstrated_terms:
            changes_explanation += f" Keep these skills prominent: {', '.join(demonstrated_terms[:6])}."

        return {
            "optimized_summary": None,
            "bullet_changes": bullet_changes,
            "changes_explanation": changes_explanation,
        }

    def extract_job_requirements(self, job_description: str) -> dict:
        from app.ai.skill_taxonomy import extract_technical_skills, extract_education_level, extract_years_experience
        return {
            "technical_skills": extract_technical_skills(job_description),
            "years_experience": extract_years_experience(job_description),
            "education_requirement": extract_education_level(job_description),
            "key_responsibilities": [],
        }
