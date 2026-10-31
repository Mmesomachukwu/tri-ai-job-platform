import hashlib
import re
from datetime import datetime

# Extensible category taxonomy (spec section 2/23) - keyword-based
# classifier so new categories/roles can be added without touching the
# matching engine or frontend.
CATEGORY_KEYWORDS = {
    "Data Science & AI": [
        "data scientist", "data analyst", "data engineer", "machine learning engineer",
        "ml engineer", "ai engineer", "ai researcher", "research scientist",
        "analytics engineer", "business intelligence",
    ],
    "Software Engineering": [
        "software engineer", "software developer", "backend engineer", "frontend engineer",
        "full stack", "fullstack", "python developer", "java developer",
        "javascript developer", "typescript developer", "react developer", "mobile developer",
    ],
    "Cloud & DevOps": [
        "cloud engineer", "cloud architect", "cloud developer", "devops", "site reliability",
        "sre", "infrastructure engineer", "platform engineer", "kubernetes engineer",
        "cloud security", "mlops",
    ],
    "Cybersecurity": [
        "cybersecurity", "security engineer", "information security", "security operations",
        "application security",
    ],
    "Data Infrastructure": [
        "database engineer", "database administrator", "dba", "data architect",
        "big data engineer", "data platform engineer",
    ],
}


def classify_category(title: str) -> str:
    title_l = (title or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in title_l for k in keywords):
            return category
    return "Other Technology"


def make_dedup_hash(title: str, company: str, location: str | None) -> str:
    key = f"{(title or '').strip().lower()}|{(company or '').strip().lower()}|{(location or '').strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _parse_years(text: str) -> float | None:
    if not text:
        return None
    m = re.search(r"(\d+)\+?\s*years?", text, re.I)
    return float(m.group(1)) if m else None


def normalize_job(raw: dict, source_name: str) -> dict:
    """Converts a provider-specific raw job dict into the common shape
    used across the app (spec section 27), plus derived fields
    (category, dedup_hash) the matching engine and DB need."""
    title = (raw.get("title") or "").strip()
    company = (raw.get("company") or "").strip()
    location = (raw.get("location") or "").strip() or None

    date_posted = raw.get("posted_date")
    if isinstance(date_posted, str):
        try:
            date_posted = datetime.fromisoformat(date_posted)
        except ValueError:
            date_posted = None
    elif isinstance(date_posted, (int, float)):
        try:
            date_posted = datetime.utcfromtimestamp(date_posted / 1000)
        except (ValueError, OSError):
            date_posted = None
    elif not isinstance(date_posted, datetime):
        date_posted = None

    return {
        "external_id": raw.get("external_id"),
        "source": source_name,
        "title": title,
        "company": company,
        "location": location,
        "category": raw.get("category") or classify_category(title),
        "description": raw.get("description"),
        "requirements": raw.get("requirements"),
        "responsibilities": raw.get("responsibilities"),
        "salary_min": raw.get("salary_min"),
        "salary_max": raw.get("salary_max"),
        "employment_type": raw.get("employment_type"),
        "remote_type": raw.get("remote_type"),
        "experience_level": raw.get("experience_level"),
        "posted_date": date_posted,
        "job_url": raw.get("job_url"),
        "dedup_hash": make_dedup_hash(title, company, location),
        "required_skills": [s.lower() for s in (raw.get("required_skills") or [])],
        "preferred_skills": [s.lower() for s in (raw.get("preferred_skills") or [])],
    }
