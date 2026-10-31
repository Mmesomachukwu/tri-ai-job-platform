from datetime import datetime
from pydantic import BaseModel


class JobOut(BaseModel):
    id: str
    title: str
    company: str
    location: str | None
    category: str | None
    description: str | None
    requirements: str | None
    responsibilities: str | None
    salary_min: float | None
    salary_max: float | None
    employment_type: str | None
    remote_type: str | None
    experience_level: str | None
    posted_date: datetime | None
    job_url: str
    source: str
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    is_saved: bool = False

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[JobOut]
