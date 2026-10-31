from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.job import Job, JobSkill, SavedJob
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, db: Session):
        super().__init__(db, Job)

    def get_by_dedup_hash(self, dedup_hash: str) -> Job | None:
        return self.db.query(Job).filter(Job.dedup_hash == dedup_hash).first()

    def search(
        self,
        keyword: str | None = None,
        category: str | None = None,
        location: str | None = None,
        remote_type: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        skills: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, list[Job]]:
        q = self.db.query(Job)

        if keyword:
            like = f"%{keyword}%"
            q = q.filter(or_(Job.title.ilike(like), Job.company.ilike(like), Job.description.ilike(like)))
        if category:
            q = q.filter(Job.category == category)
        if location:
            q = q.filter(Job.location.ilike(f"%{location}%"))
        if remote_type:
            q = q.filter(Job.remote_type == remote_type)
        if employment_type:
            q = q.filter(Job.employment_type == employment_type)
        if experience_level:
            q = q.filter(Job.experience_level == experience_level)
        if salary_min is not None:
            q = q.filter(Job.salary_max >= salary_min)
        if salary_max is not None:
            q = q.filter(Job.salary_min <= salary_max)
        if skills:
            job_ids_with_skills = (
                self.db.query(JobSkill.job_id)
                .filter(JobSkill.skill.in_([s.lower() for s in skills]))
                .distinct()
            )
            q = q.filter(Job.id.in_(job_ids_with_skills))

        q = q.order_by(Job.posted_date.desc().nullslast())
        total = q.count()
        results = q.offset((page - 1) * page_size).limit(page_size).all()
        return total, results

    def get_skills(self, job_id: str) -> tuple[list[str], list[str]]:
        rows = self.db.query(JobSkill).filter(JobSkill.job_id == job_id).all()
        required = [r.skill for r in rows if r.is_required == "true"]
        preferred = [r.skill for r in rows if r.is_required != "true"]
        return required, preferred

    def replace_skills(self, job_id: str, required: list[str], preferred: list[str]) -> None:
        self.db.query(JobSkill).filter(JobSkill.job_id == job_id).delete()
        for skill in required:
            self.db.add(JobSkill(job_id=job_id, skill=skill.lower(), is_required="true"))
        for skill in preferred:
            self.db.add(JobSkill(job_id=job_id, skill=skill.lower(), is_required="false"))
        self.db.commit()


class SavedJobRepository(BaseRepository[SavedJob]):
    def __init__(self, db: Session):
        super().__init__(db, SavedJob)

    def get_for_job(self, job_id: str) -> SavedJob | None:
        return self.db.query(SavedJob).filter(SavedJob.job_id == job_id).first()

    def list_job_ids(self) -> set[str]:
        rows = self.db.query(SavedJob.job_id).all()
        return {r[0] for r in rows}

    def list_jobs(self) -> list[Job]:
        job_ids = self.list_job_ids()
        if not job_ids:
            return []
        return self.db.query(Job).filter(Job.id.in_(job_ids)).all()
