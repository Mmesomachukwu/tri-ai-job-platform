"""
Central configuration.

Per spec: PostgreSQL is the required database (no SQLite/Mongo/Firebase
fallback). Everything else stays free/local: Ollama for the LLM,
sentence-transformers for embeddings, local filesystem for CV storage.
No Docker - this app is configured to run directly on the local machine.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    APP_NAME: str = "Tech Job AI Platform"
    ENV: str = os.getenv("ENV", "development")

    # --- Database: PostgreSQL required ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:admin@localhost:5432/job_ai"
    )

    # Single-user, local application - no authentication, no accounts.

    # --- CV storage (local filesystem - no paid object storage required) ---
    LOCAL_STORAGE_DIR: Path = BASE_DIR / "storage" / "resumes"
    MAX_CV_SIZE_MB: int = 5
    ALLOWED_CV_EXTENSIONS = {".pdf", ".docx"}

    # --- AI provider abstraction ---
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    # A small model that realistically runs on a normal dev machine
    # (not a 70B+ model requiring a GPU cluster).
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    # --- Embedding model (local, free, via sentence-transformers) ---
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # --- Job provider ---
    # RealJobProvider aggregates free/legal public API sources (RemoteOK,
    # Remotive, Greenhouse, Lever). All are keyless today; JOB_API_KEY is
    # reserved for a future source that requires one - not currently used.
    JOB_PROVIDER: str = os.getenv("JOB_PROVIDER", "real")
    JOB_API_KEY: str = os.getenv("JOB_API_KEY", "")

    # --- Scoring weights (configurable, must sum to 1.0) ---
    MATCH_WEIGHTS = {
        "technical_skills": 0.25,
        "keywords": 0.20,
        "experience": 0.20,
        "responsibilities": 0.15,
        "education": 0.10,
        "ats_structure": 0.10,
    }


settings = Settings()
