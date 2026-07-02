import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from app.models import AnalysisRequest

# Pending/running jobs older than this are presumed abandoned
JOB_TTL_SECONDS = 3600
# Terminal (completed/error) jobs are kept briefly for the polling fallback
FINISHED_TTL_SECONDS = 900
MAX_JOBS = 500

TERMINAL_STATUSES = {"completed", "error"}


@dataclass
class JobState:
    thread_id: str
    status: str = "pending"  # pending | running | completed | error
    params: Optional[AnalysisRequest] = None
    current_step: Optional[str] = None
    steps_completed: int = 0
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None


class JobManager:
    """In-memory job state tracking for analysis runs."""

    def __init__(self):
        self._jobs: dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create(self, thread_id: str, params: Optional[AnalysisRequest] = None) -> JobState:
        with self._lock:
            self._evict_locked()
            job = JobState(thread_id=thread_id, params=params)
            self._jobs[thread_id] = job
            return job

    def get(self, thread_id: str) -> Optional[JobState]:
        with self._lock:
            return self._jobs.get(thread_id)

    def update(self, thread_id: str, **kwargs) -> Optional[JobState]:
        with self._lock:
            job = self._jobs.get(thread_id)
            if job is None:
                return None
            for k, v in kwargs.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            if job.status in TERMINAL_STATUSES and job.finished_at is None:
                job.finished_at = time.time()
            return job

    def delete(self, thread_id: str):
        with self._lock:
            self._jobs.pop(thread_id, None)

    def clear(self):
        with self._lock:
            self._jobs.clear()

    def _evict_locked(self):
        """Drop expired jobs; caller must hold the lock."""
        now = time.time()
        expired = [
            tid
            for tid, job in self._jobs.items()
            if (
                job.status in TERMINAL_STATUSES
                and job.finished_at is not None
                and now - job.finished_at > FINISHED_TTL_SECONDS
            )
            or now - job.created_at > JOB_TTL_SECONDS
        ]
        for tid in expired:
            del self._jobs[tid]

        if len(self._jobs) >= MAX_JOBS:
            oldest = sorted(self._jobs.values(), key=lambda j: j.created_at)
            for job in oldest[: len(self._jobs) - MAX_JOBS + 1]:
                del self._jobs[job.thread_id]


# Shared instance
job_manager = JobManager()
