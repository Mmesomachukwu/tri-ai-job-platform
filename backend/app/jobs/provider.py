"""
Job provider abstraction (per spec section 25-26).

JOB_PROVIDER=real (default) -> RealJobProvider, aggregating free/legal
public API sources (RemoteOK, Remotive, Greenhouse, Lever) - real, current
job postings, never fabricated, never presented as demo data.

JOB_PROVIDER=mock -> MockJobProvider, clearly-labeled demo jobs. Used for
testing/development, and as an explicit, clearly-labeled fallback if the
real provider is unreachable - never silently mixed with real results.

The API/service layer only ever talks to this abstraction - swapping the
env var changes the data source with no other code changes.
"""
from abc import ABC, abstractmethod


class JobProvider(ABC):
    @abstractmethod
    def search_jobs(self, query: str | None = None, filters: dict | None = None) -> list[dict]:
        """Returns a list of raw job dicts in the common normalized shape
        (see app/jobs/normalizer.py:NORMALIZED_FIELDS)."""
        raise NotImplementedError
