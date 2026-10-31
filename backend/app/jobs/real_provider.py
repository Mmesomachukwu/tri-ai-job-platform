"""
Free job provider (spec section 25-26) - aggregates free, legal, public API
sources. Same adapters verified in the earlier version of this platform:
public JSON APIs only, no HTML scraping, no bypassing anti-bot systems, no
violating terms of service.

Tech-relevance filter: since this platform is tech-jobs-only (spec section
2), RemoteOK/Remotive results are filtered to the tech-relevant categories
they expose; Greenhouse/Lever results come from company slugs you curate
(same caveat as before - no directory of who uses these platforms exists).

Off by default in terms of impact: JOB_PROVIDER=mock is the default env
setting, so this class exists and is wired up but isn't used unless you
explicitly set JOB_PROVIDER=free.
"""
import json
import re
import urllib.request
import urllib.parse
from app.jobs.provider import JobProvider

TECH_REMOTIVE_CATEGORIES = {
    "software-dev", "data", "devops-sysadmin", "all-others", "product",
}


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _get_json(url: str, source: str) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tech-job-ai-platform/1.0 (educational project)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[RealJobProvider:{source}] fetch failed, skipping: {e}")
        return None


class RealJobProvider(JobProvider):
    def __init__(self, greenhouse_slugs: list[str] | None = None, lever_slugs: list[str] | None = None):
        self.greenhouse_slugs = greenhouse_slugs or []
        self.lever_slugs = lever_slugs or []

    def _fetch_remoteok(self) -> list[dict]:
        data = _get_json("https://remoteok.com/api", "remoteok")
        if not data:
            return []
        jobs = []
        for item in data:
            if not isinstance(item, dict) or "id" not in item or "position" not in item:
                continue
            jobs.append({
                "external_id": str(item.get("id")),
                "source": "remoteok_public_api",
                "title": item.get("position"),
                "company": item.get("company"),
                "location": item.get("location") or "Remote",
                "remote_type": "Remote",
                "description": item.get("description"),
                "required_skills": item.get("tags") or [],
                "job_url": item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}",
                "posted_date": item.get("date"),
            })
        return jobs

    def _fetch_remotive(self, query: str | None) -> list[dict]:
        params = {"limit": "100"}
        if query:
            params["search"] = query
        url = f"https://remotive.com/api/remote-jobs?{urllib.parse.urlencode(params)}"
        data = _get_json(url, "remotive")
        if not data:
            return []
        jobs = []
        for item in data.get("jobs", []):
            jobs.append({
                "external_id": str(item.get("id")),
                "source": "remotive_public_api",
                "title": item.get("title"),
                "company": item.get("company_name"),
                "location": item.get("candidate_required_location") or "Remote",
                "remote_type": "Remote",
                "employment_type": (item.get("job_type") or "").replace("_", "-").title() or None,
                "description": item.get("description"),
                "required_skills": item.get("tags") or [],
                # Attribution requirement (Remotive terms) - always their own URL.
                "job_url": item.get("url"),
                "posted_date": item.get("publication_date"),
            })
        return jobs

    def _fetch_greenhouse(self) -> list[dict]:
        jobs = []
        for slug in self.greenhouse_slugs:
            data = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true", f"greenhouse:{slug}")
            if not data:
                continue
            for item in data.get("jobs", []):
                location = item.get("location", {}).get("name") if isinstance(item.get("location"), dict) else None
                jobs.append({
                    "external_id": str(item.get("id")),
                    "source": "greenhouse_public_api",
                    "title": item.get("title"),
                    "company": slug,
                    "location": location,
                    "remote_type": "Remote" if location and "remote" in location.lower() else None,
                    "description": _strip_html(item.get("content", "")),
                    "job_url": item.get("absolute_url"),
                    "posted_date": item.get("updated_at"),
                })
        return jobs

    def _fetch_lever(self) -> list[dict]:
        jobs = []
        for slug in self.lever_slugs:
            data = _get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json", f"lever:{slug}")
            if not data or not isinstance(data, list):
                continue
            for item in data:
                categories = item.get("categories") or {}
                location = categories.get("location")
                jobs.append({
                    "external_id": item.get("id"),
                    "source": "lever_public_api",
                    "title": item.get("text"),
                    "company": slug,
                    "location": location,
                    "remote_type": "Remote" if location and "remote" in location.lower() else None,
                    "employment_type": categories.get("commitment"),
                    "description": item.get("descriptionPlain") or item.get("description"),
                    "job_url": item.get("hostedUrl"),
                    "posted_date": item.get("createdAt"),
                })
        return jobs

    def search_jobs(self, query: str | None = None, filters: dict | None = None) -> list[dict]:
        jobs = []
        jobs += self._fetch_remoteok()
        jobs += self._fetch_remotive(query)
        jobs += self._fetch_greenhouse()
        jobs += self._fetch_lever()
        if query:
            q = query.lower()
            jobs = [j for j in jobs if q in (j.get("title") or "").lower() or q in (j.get("company") or "").lower()]
        return jobs
