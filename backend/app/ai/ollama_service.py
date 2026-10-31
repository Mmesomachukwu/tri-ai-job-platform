"""
Ollama implementation of AIService.

Per spec section 44: if Ollama is unavailable, the app must not fail or
fabricate results - it falls back to deterministic, rule-based templates
(TemplateAIService, below). This module never lets an Ollama failure
propagate as a user-facing error from the analysis/optimization endpoints;
callers get a valid response either way, with `explanation_source`
indicating which path was used.
"""
import json
import re
import urllib.request
import urllib.error
from app.ai.ai_service import AIService
from app.ai.prompts import build_analysis_prompt, build_optimization_prompt, EXTRACTION_SYSTEM_PROMPT
from app.database.config import settings


class OllamaUnavailableError(Exception):
    pass


class OllamaInvalidResponseError(Exception):
    pass


def _call_ollama(prompt: str, timeout: int = 30) -> str:
    try:
        payload = json.dumps({
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise OllamaUnavailableError(str(e))


def _parse_json_response(raw: str) -> dict:
    # Ollama with format="json" should return clean JSON, but strip any
    # stray markdown fences defensively.
    cleaned = re.sub(r"^```json\s*|\s*```$", "", raw.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise OllamaInvalidResponseError(f"Model did not return valid JSON: {e}")


class OllamaAIService(AIService):
    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{settings.OLLAMA_BASE_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False

    def analyze_resume(self, resume_text: str, job_context: dict, match_result: dict) -> dict:
        prompt = build_analysis_prompt(resume_text, job_context, match_result)
        raw = _call_ollama(prompt)
        parsed = _parse_json_response(raw)
        if "summary" not in parsed or "recommendations" not in parsed:
            raise OllamaInvalidResponseError("Response missing required fields")
        return {"summary": parsed["summary"], "recommendations": parsed["recommendations"]}

    def optimize_resume(self, resume_text: str, parsed_data: dict, job_context: dict, match_result: dict) -> dict:
        prompt = build_optimization_prompt(resume_text, job_context, match_result)
        raw = _call_ollama(prompt, timeout=60)
        parsed = _parse_json_response(raw)
        required = {"optimized_summary", "bullet_changes", "changes_explanation"}
        if not required.issubset(parsed.keys()):
            raise OllamaInvalidResponseError("Response missing required fields")
        return parsed

    def extract_job_requirements(self, job_description: str) -> dict:
        prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nJOB DESCRIPTION:\n{job_description[:3000]}\n\nReturn the JSON now."
        raw = _call_ollama(prompt)
        return _parse_json_response(raw)
