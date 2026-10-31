"""
Application entrypoint. No Docker - run directly with:
    uvicorn app.main:app --reload
"""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.config import settings
from app.api.router import api_router

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("tech_job_platform")


def _warn_if_migrations_pending():
    """
    Startup safety check: compares the DB's current Alembic revision
    against the latest available migration script and logs a clear
    warning if they don't match, rather than silently running against a
    stale/missing schema. Never auto-runs migrations itself - schema
    changes should always be an explicit `alembic upgrade head` step.
    """
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from sqlalchemy import text
        from app.database.session import engine

        backend_dir = Path(__file__).resolve().parent.parent
        alembic_cfg = Config(str(backend_dir / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
        script = ScriptDirectory.from_config(alembic_cfg)
        head_revision = script.get_current_head()

        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT version_num FROM alembic_version LIMIT 1"
            )).fetchone()
            current_revision = result[0] if result else None

        if current_revision != head_revision:
            logger.warning(
                f"Database schema revision ({current_revision}) does not match the "
                f"latest migration ({head_revision}). Run `alembic upgrade head` before "
                f"using the app."
            )
        else:
            logger.info(f"Schema up to date (revision {current_revision}).")
    except Exception as e:
        logger.warning(f"Could not verify migration status: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")

    from app.database.session import check_db_connection

    ok, error = check_db_connection()
    if ok:
        logger.info("Database connected.")
        _warn_if_migrations_pending()
    else:
        logger.error(f"Database connection failed: {error}")
        logger.error("Check PostgreSQL is running and DATABASE_URL is correct.")

    ai_provider_note = "Ollama" if settings.AI_PROVIDER == "ollama" else settings.AI_PROVIDER
    from app.ai.factory import get_ai_service
    _, source = get_ai_service()
    if source == "template":
        logger.warning(
            f"AI_PROVIDER is '{settings.AI_PROVIDER}' but Ollama is not reachable at "
            f"{settings.OLLAMA_BASE_URL} - falling back to deterministic templates for "
            f"explanations. Run `ollama serve` and pull {settings.OLLAMA_MODEL} to enable AI-generated text."
        )
    else:
        logger.info(f"AI service ready via {ai_provider_note} ({settings.OLLAMA_MODEL}).")

    logger.info(f"Job provider: {settings.JOB_PROVIDER}")
    logger.info("All services initialized.")

    yield

    logger.info("Shutting down...")
    from app.database.session import close_db
    close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered technology job search and CV/ATS compatibility analysis.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health():
    from app.database.session import check_db_connection
    from app.ai.factory import get_ai_service

    db_ok, db_error = check_db_connection()
    _, ai_source = get_ai_service()

    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "database": "connected" if db_ok else f"error: {db_error}",
        "ai_explanation_source": ai_source,  # "ollama" or "template"
        "job_provider": settings.JOB_PROVIDER,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENV", "development") == "development"
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload)
