from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class JobRecord:
    job_id: str
    job_type: str
    status: str = "pending"
    message: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def create_job(self, job_type: str, metadata: Optional[dict] = None) -> JobRecord:
        job_id = uuid.uuid4().hex
        record = JobRecord(job_id=job_id, job_type=job_type, metadata=metadata or {})
        with self._lock:
            self._jobs[job_id] = record
        return record

    def update_job(self, job_id: str, status: str, message: str | None = None, metadata: Optional[dict] = None) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return
            record.status = status
            record.updated_at = time.time()
            if message:
                record.message = message
            if metadata:
                record.metadata.update(metadata)

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def pending_jobs(self) -> int:
        with self._lock:
            return sum(1 for job in self._jobs.values() if job.status not in {"completed", "failed"})


job_manager = JobManager()
