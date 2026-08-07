"""Operations / observability routes: /api/metrics + /api/ops/status."""
import psutil
from fastapi import APIRouter

from services.metrics import metrics
from services.stock_data import cache_stats
from services.task_manager import task_manager
from services.market_stream import market_stream

router = APIRouter()


@router.get("/api/metrics")
def get_metrics():
    stream = market_stream.get_status()
    tasks = task_manager.list_tasks(limit=10)
    return {
        "api": metrics.snapshot(),
        "cache": cache_stats(),
        "stream": {
            "running": stream["running"],
            "active_symbols": stream["active_symbols"],
            "subscribers": stream["subscribers"],
        },
        "tasks": {
            "total": len(tasks),
            "running": sum(1 for t in tasks if t["status"] == "RUNNING"),
            "recent": tasks,
        },
    }


@router.get("/api/ops/status")
def ops_status():
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        mem_used_mb = round(mem.used / (1024 * 1024), 1)
        mem_total_mb = round(mem.total / (1024 * 1024), 1)
    except Exception:
        cpu, mem_used_mb, mem_total_mb = 0.0, 0.0, 0.0
    return {
        "ok": True,
        "uptime_sec": metrics.snapshot()["uptime_sec"],
        "cpu_percent": cpu,
        "memory_mb": {"used": mem_used_mb, "total": mem_total_mb},
        "stream_running": market_stream.get_status()["running"],
        "active_background_tasks": len([t for t in task_manager.list_tasks(limit=50) if t["status"] in ("QUEUED", "RUNNING")]),
    }
