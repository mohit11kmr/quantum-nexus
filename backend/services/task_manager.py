"""
Background Task Manager.

Runs long-lived jobs (brain optimize, heavy backtests) in daemon threads so the
FastAPI event loop and threadpool stay responsive. The client receives a task_id
immediately and polls /api/brain/tasks/{id} for status/progress.

Single-process friendly (no Redis/Celery required), which fits Render's free tier.
"""

import threading
import time
import uuid
from typing import Any, Callable, Dict, Optional

TASK_TTL_SEC = 3600.0


class BackgroundTaskManager:
    def __init__(self) -> None:
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> str:
        task_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._tasks[task_id] = {
                "id": task_id,
                "status": "QUEUED",
                "progress": 0,
                "result": None,
                "error": None,
                "created_at": time.time(),
                "updated_at": time.time(),
            }
        thread = threading.Thread(
            target=self._run, args=(task_id, fn, args, kwargs), daemon=True
        )
        thread.start()
        return task_id

    def _run(self, task_id: str, fn: Callable, args: tuple, kwargs: dict) -> None:
        self._update(task_id, status="RUNNING", progress=10)
        try:
            result = fn(*args, **kwargs)
            self._update(task_id, status="SUCCEEDED", progress=100, result=result)
        except Exception as exc:  # noqa: BLE001 - surfaced to the client
            self._update(task_id, status="FAILED", error=str(exc))
        finally:
            self._prune()

    def update_progress(self, task_id: str, progress: int, note: Optional[str] = None) -> None:
        fields: Dict[str, Any] = {"progress": max(0, min(100, int(progress)))}
        if note:
            fields["note"] = str(note)
        self._update(task_id, **fields)

    def _update(self, task_id: str, **fields: Any) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            task.update(fields)
            task["updated_at"] = time.time()

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            task = self._tasks.get(task_id)
            return dict(task) if task else None

    def list_tasks(self, limit: int = 20) -> list:
        with self._lock:
            items = sorted(self._tasks.values(), key=lambda t: t["created_at"], reverse=True)
            return [dict(t) for t in items[:limit]]

    def _prune(self) -> None:
        cutoff = time.time() - TASK_TTL_SEC
        with self._lock:
            for tid in [tid for tid, t in self._tasks.items() if t.get("created_at", 0) < cutoff]:
                self._tasks.pop(tid, None)


task_manager = BackgroundTaskManager()
