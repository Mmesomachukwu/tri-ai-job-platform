from sqlalchemy.orm import Session
from app.models.analysis import Analysis
from app.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository[Analysis]):
    def __init__(self, db: Session):
        super().__init__(db, Analysis)

    def get_latest(self, resume_id: str, job_id: str) -> Analysis | None:
        return (
            self.db.query(Analysis)
            .filter(Analysis.resume_id == resume_id, Analysis.job_id == job_id)
            .order_by(Analysis.created_at.desc())
            .first()
        )

    def list_all(self, limit: int = 20) -> list[Analysis]:
        return self.db.query(Analysis).order_by(Analysis.created_at.desc()).limit(limit).all()
