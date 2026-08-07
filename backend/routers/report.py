"""Automated daily report routes."""
from fastapi import APIRouter

from services.daily_report import daily_report_scheduler, _next_scheduled_run

router = APIRouter()


@router.get("/api/report/daily")
def get_daily_report():
    latest = daily_report_scheduler.get_latest()
    return {
        "report": latest,
        "next_run_ist": _next_scheduled_run(),
        "auto_enabled": True,
        "schedule": "weekdays 15:30 IST (market close)",
    }


@router.post("/api/report/daily/generate")
def generate_daily_report():
    report = daily_report_scheduler.force_generate()
    return {"report": report, "posted": report.get("posted")}
