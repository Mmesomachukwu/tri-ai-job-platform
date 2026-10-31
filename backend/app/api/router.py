from fastapi import APIRouter
from app.api import jobs, resumes, analyses

api_router = APIRouter()
api_router.include_router(jobs.router)
api_router.include_router(jobs.saved_router)
api_router.include_router(resumes.router)
api_router.include_router(analyses.router)
