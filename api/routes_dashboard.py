from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from database.session import get_db
from database.models import Task, TaskStatus, AgentLog, TestResult, PullRequest, DockerSession, AuditLog, Notification

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_tasks = db.query(func.count(Task.id)).scalar() or 0
    completed_tasks = db.query(func.count(Task.id)).filter(Task.status == TaskStatus.COMPLETED.value).scalar() or 0
    failed_tasks = db.query(func.count(Task.id)).filter(Task.status.in_([TaskStatus.FAILED.value, TaskStatus.ESCALATED.value])).scalar() or 0
    running_tasks = db.query(func.count(Task.id)).filter(Task.status == TaskStatus.RUNNING.value).scalar() or 0
    
    total_retries = db.query(func.sum(Task.retry_count)).scalar() or 0
    avg_confidence = db.query(func.avg(Task.confidence_score)).scalar() or 0.95

    active_task = db.query(Task).filter(Task.status == TaskStatus.RUNNING.value).order_by(Task.updated_at.desc()).first()
    running_agent = active_task.current_agent if active_task else "Idle"

    return {
        "running_agent": running_agent,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "running_tasks": running_tasks,
        "total_retries": int(total_retries),
        "average_confidence": round(float(avg_confidence) * 100, 1),
        "active_task_id": active_task.id if active_task else None
    }

@router.get("/audit-logs")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return logs

@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    notifs = db.query(Notification).order_by(Notification.id.desc()).limit(20).all()
    return notifs
