import time
from concurrent.futures import ThreadPoolExecutor

from app.models import AnalysisRequest
from app.services import job_manager as jm
from app.services.job_manager import JobManager


class TestJobManagerBasics:
    def test_create_get_round_trip(self):
        mgr = JobManager()
        params = AnalysisRequest(crypto_name="ethereum", currency="eur", days=90)
        job = mgr.create("t1", params=params)

        fetched = mgr.get("t1")
        assert fetched is job
        assert fetched.status == "pending"
        assert fetched.params.crypto_name == "ethereum"

    def test_get_unknown_returns_none(self):
        mgr = JobManager()
        assert mgr.get("missing") is None

    def test_update_unknown_returns_none_and_does_not_create(self):
        mgr = JobManager()
        assert mgr.update("missing", status="running") is None
        assert mgr.get("missing") is None

    def test_update_ignores_unknown_attributes(self):
        mgr = JobManager()
        mgr.create("t1")
        job = mgr.update("t1", status="running", bogus_field="x")
        assert job.status == "running"
        assert not hasattr(job, "bogus_field")

    def test_delete(self):
        mgr = JobManager()
        mgr.create("t1")
        mgr.delete("t1")
        assert mgr.get("t1") is None

    def test_delete_unknown_is_noop(self):
        mgr = JobManager()
        mgr.delete("missing")  # must not raise

    def test_clear(self):
        mgr = JobManager()
        mgr.create("t1")
        mgr.create("t2")
        mgr.clear()
        assert mgr.get("t1") is None
        assert mgr.get("t2") is None

    def test_terminal_status_sets_finished_at(self):
        mgr = JobManager()
        mgr.create("t1")
        job = mgr.update("t1", status="completed")
        assert job.finished_at is not None

        running = mgr.create("t2")
        mgr.update("t2", status="running")
        assert running.finished_at is None


class TestJobManagerEviction:
    def test_stale_pending_job_evicted(self, monkeypatch):
        mgr = JobManager()
        now = time.time()
        mgr.create("old")
        mgr.get("old").created_at = now - jm.JOB_TTL_SECONDS - 1

        mgr.create("new")
        assert mgr.get("old") is None
        assert mgr.get("new") is not None

    def test_finished_job_evicted_sooner(self):
        mgr = JobManager()
        now = time.time()
        mgr.create("done")
        mgr.update("done", status="completed")
        mgr.get("done").finished_at = now - jm.FINISHED_TTL_SECONDS - 1

        mgr.create("new")
        assert mgr.get("done") is None

    def test_fresh_jobs_not_evicted(self):
        mgr = JobManager()
        mgr.create("fresh")
        mgr.update("fresh", status="completed")
        mgr.create("new")
        assert mgr.get("fresh") is not None

    def test_max_jobs_cap_evicts_oldest(self, monkeypatch):
        monkeypatch.setattr(jm, "MAX_JOBS", 5)
        mgr = JobManager()
        for i in range(5):
            job = mgr.create(f"t{i}")
            job.created_at = time.time() - (100 - i)

        mgr.create("newest")
        assert len(mgr._jobs) <= 5
        assert mgr.get("t0") is None
        assert mgr.get("newest") is not None


class TestJobManagerConcurrency:
    def test_concurrent_mixed_operations(self):
        mgr = JobManager()

        def worker(i: int):
            tid = f"t{i % 10}"
            mgr.create(tid)
            mgr.update(tid, status="running", steps_completed=i)
            mgr.get(tid)
            if i % 3 == 0:
                mgr.delete(tid)

        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(worker, range(200)))

        # Surviving jobs must be internally consistent
        for job in list(mgr._jobs.values()):
            assert job.thread_id.startswith("t")
            assert job.status in {"pending", "running", "completed", "error"}
