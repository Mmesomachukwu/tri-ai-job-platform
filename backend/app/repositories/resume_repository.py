from sqlalchemy.orm import Session
from app.models.resume import Resume, ResumeVersion, ResumeSkill
from app.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    def __init__(self, db: Session):
        super().__init__(db, Resume)

    def list_all(self) -> list[Resume]:
        """Single-tenant app - all resumes belong to the local application,
        no user scoping."""
        return self.db.query(Resume).order_by(Resume.created_at.desc()).all()

    def replace_skills(self, resume_id: str, skills: list[str]) -> None:
        self.db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume_id).delete()
        for skill in skills:
            self.db.add(ResumeSkill(resume_id=resume_id, skill=skill))
        self.db.commit()

    def get_skills(self, resume_id: str) -> list[str]:
        rows = self.db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume_id).all()
        return [r.skill for r in rows]

    def create_version(self, **kwargs) -> ResumeVersion:
        version = ResumeVersion(**kwargs)
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def list_versions(self, resume_id: str) -> list[ResumeVersion]:
        return (
            self.db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.created_at.desc())
            .all()
        )
