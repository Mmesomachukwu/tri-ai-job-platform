"""
CV upload, storage, and structured extraction (spec section 20-21).

Free/open-source only: PyMuPDF for PDF, python-docx for DOCX, regex +
curated taxonomy for structuring (no paid parsing API).
"""
import re
import uuid
from pathlib import Path
from app.database.config import settings


class ResumeValidationError(Exception):
    pass


def validate_upload(filename: str, size_bytes: int) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_CV_EXTENSIONS:
        raise ResumeValidationError(f"Unsupported file type '{ext}'. Allowed: PDF, DOCX.")
    if size_bytes > settings.MAX_CV_SIZE_MB * 1024 * 1024:
        raise ResumeValidationError(f"File exceeds the {settings.MAX_CV_SIZE_MB}MB size limit.")
    return ext.lstrip(".")


def save_file(file_bytes: bytes, filename: str) -> str:
    settings.LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    # Path traversal prevention: strip any directory components from the
    # client-supplied filename before using it - Path(x) / "../../etc/passwd"
    # would otherwise happily escape LOCAL_STORAGE_DIR.
    safe_filename = Path(filename).name
    unique_name = f"{uuid.uuid4().hex}_{safe_filename}"
    dest = (settings.LOCAL_STORAGE_DIR / unique_name).resolve()
    if not str(dest).startswith(str(settings.LOCAL_STORAGE_DIR.resolve())):
        raise ResumeValidationError("Invalid filename.")
    with open(dest, "wb") as f:
        f.write(file_bytes)
    return str(dest)


def extract_text_pdf(path: str) -> str:
    import fitz
    parts = []
    with fitz.open(path) as doc:
        for page in doc:
            parts.append(page.get_text())
    return "\n".join(parts).strip()


def extract_text_docx(path: str) -> str:
    import docx
    document = docx.Document(path)
    return "\n".join(p.text for p in document.paragraphs).strip()


def extract_text(path: str, file_type: str) -> str:
    if file_type == "pdf":
        return extract_text_pdf(path)
    if file_type == "docx":
        return extract_text_docx(path)
    raise ResumeValidationError(f"Unsupported file type: {file_type}")


# --- Structured field extraction (regex-based, free/local) ---

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
_LINKEDIN_RE = re.compile(r"(https?://)?(www\.)?linkedin\.com/in/[\w-]+", re.I)
_GITHUB_RE = re.compile(r"(https?://)?(www\.)?github\.com/[\w-]+", re.I)


def extract_contact_info(text: str) -> dict:
    email = _EMAIL_RE.search(text)
    phone = _PHONE_RE.search(text)
    linkedin = _LINKEDIN_RE.search(text)
    github = _GITHUB_RE.search(text)
    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "linkedin": linkedin.group(0) if linkedin else None,
        "github": github.group(0) if github else None,
    }


def structure_resume_text(raw_text: str) -> dict:
    from app.ai.skill_taxonomy import extract_technical_skills, extract_soft_skills, extract_education_level
    from app.ai.skill_taxonomy import extract_years_experience

    contact = extract_contact_info(raw_text)
    technical_skills = extract_technical_skills(raw_text)
    soft_skills = extract_soft_skills(raw_text)
    education_level = extract_education_level(raw_text)
    years_experience = extract_years_experience(raw_text)

    return {
        "contact": contact,
        "technical_skills": technical_skills,
        "soft_skills": soft_skills,
        "education_level": education_level,
        "years_experience": years_experience,
        # Structure-level ATS heuristics (spec section 48) - observational
        # only, never a pass/fail guarantee.
        "structure_notes": check_structure(raw_text),
    }


def check_structure(text: str) -> list[str]:
    notes = []
    if not _EMAIL_RE.search(text):
        notes.append("No email address detected - make sure contact info is in plain text, not an image.")
    lower = text.lower()
    has_headers = any(h in lower for h in ["experience", "education", "skills"])
    if not has_headers:
        notes.append("Standard section headings (Experience, Education, Skills) were not clearly detected.")
    if len(text.strip()) < 200:
        notes.append("Very little text was extracted - the file may rely heavily on images, tables, or graphics that don't parse well in most ATS systems.")
    return notes


def process_resume_file(path: str, file_type: str) -> dict:
    try:
        raw_text = extract_text(path, file_type)
        if not raw_text or len(raw_text.strip()) < 20:
            return {
                "extraction_status": "failed",
                "extraction_error": "No readable text could be extracted. The file may be a scanned image or corrupted.",
                "parsed_text": None,
                "parsed_data": None,
            }
        structured = structure_resume_text(raw_text)
        return {
            "extraction_status": "success",
            "extraction_error": None,
            "parsed_text": raw_text,
            "parsed_data": structured,
        }
    except Exception as e:
        return {
            "extraction_status": "failed",
            "extraction_error": f"Could not process this file: {e}",
            "parsed_text": None,
            "parsed_data": None,
        }


def upload_and_process_resume(db, filename: str, file_bytes: bytes, label: str | None = None):
    from app.repositories.resume_repository import ResumeRepository

    file_type = validate_upload(filename, len(file_bytes))
    storage_path = save_file(file_bytes, filename)
    result = process_resume_file(storage_path, file_type)

    repo = ResumeRepository(db)
    resume = repo.create(
        filename=filename,
        file_path=storage_path,
        label=label,
        **result,
    )
    if result["extraction_status"] == "success":
        skills = result["parsed_data"]["technical_skills"] + result["parsed_data"]["soft_skills"]
        repo.replace_skills(resume.id, skills)
    return resume
