from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.database.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> tuple[bool, str | None]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)


def close_db():
    engine.dispose()


def init_db_tables():
    """
    Creates tables if they don't exist yet. For production, prefer running
    Alembic migrations (`alembic upgrade head`) instead - this exists so
    the app is runnable immediately in dev without a migration step, and
    is idempotent (safe to call on every startup).
    """
    from app.models import job, resume, analysis  # noqa: F401
    Base.metadata.create_all(bind=engine)
