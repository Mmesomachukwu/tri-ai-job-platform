"""
Tech-focused skill taxonomy (spec section 24) + rule-based extraction.
Free, local, no external API. Extensible list - not hard-coded into the
frontend (spec section 24), so new technologies can be added here without
touching UI code.
"""
import re

TECHNICAL_SKILLS = [
    "python", "r", "sql", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "react", "angular", "vue", "node.js", "fastapi", "django", "flask", "spring boot",
    "aws", "azure", "google cloud", "gcp", "docker", "kubernetes", "terraform",
    "git", "ci/cd", "postgresql", "mysql", "mongodb", "redis", "spark", "databricks",
    "snowflake", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "machine learning", "deep learning", "nlp", "computer vision", "mlops",
    "rest api", "graphql", "microservices", "linux", "bash", "airflow", "etl",
    "html", "css", "tailwind", "vite", "webpack", "jenkins", "ansible",
    "statistics", "a/b testing", "data visualization", "tableau", "power bi",
    "cybersecurity", "network security", "incident response", "siem", "cloud security",
    "system design", "agile", "scrum", "unit testing", "test automation",
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem solving", "collaboration",
    "critical thinking", "mentoring", "stakeholder management", "time management",
]

_EDU_RANK = {
    "phd": 6, "doctorate": 6, "master": 5, "msc": 5, "ma": 5, "mba": 5,
    "bachelor": 4, "bsc": 4, "ba": 4, "associate degree": 3, "diploma": 2, "high school": 1,
}


def _find_terms(text: str, vocabulary: list[str]) -> list[str]:
    text_l = (text or "").lower()
    found = []
    for term in vocabulary:
        pattern = re.escape(term).replace(r"\ ", r"[\s\-]+")
        # Allow a trailing "s" (APIs, frameworks, databases...) without
        # over-matching unrelated longer words.
        if re.search(rf"(?<![a-zA-Z0-9]){pattern}s?(?![a-zA-Z0-9])", text_l):
            found.append(term)
    return sorted(set(found))


def extract_technical_skills(text: str) -> list[str]:
    return _find_terms(text, TECHNICAL_SKILLS)


def extract_soft_skills(text: str) -> list[str]:
    return _find_terms(text, SOFT_SKILLS)


def extract_education_level(text: str) -> str | None:
    found = _find_terms(text, list(_EDU_RANK.keys()))
    if not found:
        return None
    return max(found, key=lambda t: _EDU_RANK.get(t, 0))


def education_rank(level: str | None) -> int:
    return _EDU_RANK.get((level or "").lower(), 0)


def extract_years_experience(text: str) -> float | None:
    if not text:
        return None
    candidates = []
    for m in re.finditer(r"(\d+)\+?\s*years?", text, re.I):
        candidates.append(int(m.group(1)))
    plausible = [c for c in candidates if 0 <= c <= 40]
    return float(max(plausible)) if plausible else None


def find_evidence_snippet(term: str, text: str, context_chars: int = 60) -> str | None:
    """Returns the actual CV text surrounding a matched term, used as
    cv_evidence in KeywordFinding - never fabricated, always a real excerpt."""
    if not text:
        return None
    pattern = re.escape(term).replace(r"\ ", r"[\s\-]+")
    m = re.search(rf"(?<![a-zA-Z0-9]){pattern}s?(?![a-zA-Z0-9])", text, re.I)
    if not m:
        return None
    start = max(0, m.start() - context_chars)
    end = min(len(text), m.end() + context_chars)
    snippet = text[start:end].strip().replace("\n", " ")
    return ("..." if start > 0 else "") + snippet + ("..." if end < len(text) else "")
