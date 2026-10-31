from datetime import datetime
from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: str
    filename: str
    label: str | None
    extraction_status: str
    extraction_error: str | None
    parsed_data: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeVersionOut(BaseModel):
    id: str
    resume_id: str
    job_id: str | None
    version_name: str
    content: dict
    created_at: datetime

    class Config:
        from_attributes = True
