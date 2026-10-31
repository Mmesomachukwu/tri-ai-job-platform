"""
Returns the AIService implementation to use. This is the only place that
decides Ollama vs. template - every caller elsewhere just gets an
AIService and doesn't know or care which one it is.
"""
from app.ai.ai_service import AIService
from app.ai.ollama_service import OllamaAIService
from app.ai.template_service import TemplateAIService
from app.database.config import settings

_ollama = OllamaAIService()
_template = TemplateAIService()


def get_ai_service() -> tuple[AIService, str]:
    """Returns (service, source_label). source_label is stored on the
    Analysis row so the UI can be transparent about which path produced
    the explanation text (spec section 44's honesty requirement)."""
    if settings.AI_PROVIDER == "ollama" and _ollama.is_available():
        return _ollama, "ollama"
    return _template, "template"
