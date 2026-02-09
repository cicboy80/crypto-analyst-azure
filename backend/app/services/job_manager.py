from dataclasses import dataclass, field
from typing import Any, Optional
import threading


@dataclass
class JobState:
    thread_id: str
    status: str = "pending"  # pending | running | completed | error
    current_step: Optional[str] = None
    steps_completed: int = 0
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class JobManager:
    """In-memory job state tracking for analysis runs."""

    def __init__(self):
        self._jobs: dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create(self, thread_id: str) -> JobState:
        with self._lock:
            job = JobState(thread_id=thread_id)
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
            return job

    def delete(self, thread_id: str):
        with self._lock:
            self._jobs.pop(thread_id, None)


# Shared instance
job_manager = JobManager()
