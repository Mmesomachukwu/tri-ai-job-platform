from sqlalchemy.orm import Session
from app.models.job import Job
from app.repositories.job_repository import JobRepository, SavedJobRepository
from app.jobs.provider import JobProvider
from app.jobs.real_provider import RealJobProvider
from app.jobs.normalizer import normalize_job


class JobProviderUnavailableError(Exception):
    """Raised when the real job provider returns no usable results - e.g.
    all upstream sources (RemoteOK/Remotive/Greenhouse/Lever) are
    unreachable. Per spec section 5/37, the app must NEVER silently
    substitute mock/fake jobs when this happens - the API layer turns
    this into a clear 503 with an honest message instead."""
    pass


def get_provider() -> JobProvider:
    """Job provider abstraction (spec section 6) - the rest of the app
    only ever talks to this function's return value, never to a concrete
    provider class directly. RealJobProvider is the only production
    provider; there is no mock fallback in the running application."""
    return RealJobProvider()


def sync_jobs(db: Session, query: str | None = None) -> dict:
    """
    Pulls real jobs from the configured provider, normalizes, and upserts
    into the database (dedup by title+company+location hash).

    Raises JobProviderUnavailableError if zero jobs come back - this is a
    deliberate hard stop, not a soft-fail, so the API can surface "Unable
    to retrieve real jobs right now" rather than serving an empty or
    fabricated result silently.
    """
    provider = get_provider()
    repo = JobRepository(db)
    raw_jobs = provider.search_jobs(query=query)

    if not raw_jobs:
        raise JobProviderUnavailableError(
            "Unable to retrieve real jobs right now. Please try again later."
        )

    created, updated, skipped = 0, 0, 0
    for raw in raw_jobs:
        source = raw.get("source", "unknown")
        normalized = normalize_job(raw, source)
        if not normalized["title"] or not normalized["company"] or not normalized["job_url"]:
            skipped += 1
            continue

        required = normalized.pop("required_skills")
        preferred = normalized.pop("preferred_skills")

        existing = repo.get_by_dedup_hash(normalized["dedup_hash"])
        if existing:
            job = repo.update(existing, **normalized)
            updated += 1
        else:
            job = repo.create(**normalized)
            created += 1
        repo.replace_skills(job.id, required, preferred)

    return {"created": created, "updated": updated, "skipped": skipped, "total_fetched": len(raw_jobs)}


def search_jobs(db: Session, **filters) -> tuple[int, list[dict]]:
    repo = JobRepository(db)
    total, jobs = repo.search(**filters)

    saved_ids = SavedJobRepository(db).list_job_ids()
    results = []
    for job in jobs:
        required, preferred = repo.get_skills(job.id)
        results.append({
            **job.__dict__,
            "required_skills": required,
            "preferred_skills": preferred,
            "is_saved": job.id in saved_ids,
        })
    return total, results


def get_job(db: Session, job_id: str) -> dict | None:
    repo = JobRepository(db)
    job = repo.get(job_id)
    if not job:
        return None
    required, preferred = repo.get_skills(job.id)
    saved_ids = SavedJobRepository(db).list_job_ids()
    return {
        **job.__dict__,
        "required_skills": required,
        "preferred_skills": preferred,
        "is_saved": job.id in saved_ids,
    }
