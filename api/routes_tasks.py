from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import datetime

from database.session import get_db
from database.models import (
    Task, TaskStatus, AgentLog, TestResult, PullRequest, DockerSession,
    AuditLog, Notification, RetryHistory, User
)
from orchestrator.state import PipelineExecutionState
from orchestrator.graph import DevOpsAgentOrchestrator
from api.websocket_manager import ws_manager
from config import settings

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

class TaskCreateRequest(BaseModel):
    title: str
    description: str
    project_id: Optional[int] = None

def run_pipeline_task(task_id: int):
    """Background execution of the autonomous DevOps multi-agent pipeline."""
    from database.session import SessionLocal
    db: Session = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        task.status = TaskStatus.RUNNING.value
        db.commit()

        # Workspace directory for this task
        workspace_dir = settings.SANDBOX_WORKSPACE_DIR / f"task_{task_id}"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        initial_state = PipelineExecutionState(
            task_id=task.id,
            title=task.title,
            description=task.description,
            workspace_path=str(workspace_dir.resolve())
        )

        # Audit log for initiation
        audit = AuditLog(
            task_id=task.id,
            action="TASK_START",
            actor="Orchestrator",
            payload=f"Initiating autonomous DevOps pipeline for task: '{task.title}'"
        )
        db.add(audit)
        db.commit()

        orchestrator = DevOpsAgentOrchestrator()
        final_state = orchestrator.run(initial_state)

        # Save results to DB
        task.status = final_state.status
        task.confidence_score = final_state.confidence_score
        task.retry_count = final_state.retry_count
        task.current_agent = final_state.current_agent

        # Log entry
        log_entry = AgentLog(
            task_id=task.id,
            agent_name=final_state.current_agent,
            level="INFO" if not final_state.is_escalated else "WARNING",
            message=f"Pipeline finished with status: {final_state.status}. Reason: {final_state.escalation_reason or 'Success'}"
        )
        db.add(log_entry)

        # Test results
        if final_state.test_results:
            tr = TestResult(
                task_id=task.id,
                passed_count=final_state.test_results.get("passed_count", 0),
                failed_count=final_state.test_results.get("failed_count", 0),
                test_output=final_state.test_results.get("output", ""),
                coverage=85.0
            )
            db.add(tr)

        # Pull Request
        if final_state.pr_info:
            pr = PullRequest(
                task_id=task.id,
                github_pr_url=final_state.pr_info.get("html_url"),
                pr_number=final_state.pr_info.get("pr_number"),
                branch_name=f"devops-fix/task-{task.id}",
                status=final_state.pr_info.get("status", "OPEN"),
                patch_diff=final_state.patch_diff
            )
            db.add(pr)

        # Escalation Notification
        if final_state.is_escalated:
            notif = Notification(
                task_id=task.id,
                type="ESCALATION",
                message=f"Task #{task.id} escalated: {final_state.escalation_reason}"
            )
            db.add(notif)

        # Audit log for finish
        audit_end = AuditLog(
            task_id=task.id,
            action="TASK_FINISH",
            actor=final_state.current_agent,
            guardrail_status="BLOCKED" if final_state.is_escalated else "PASSED",
            payload=f"Status: {final_state.status}, Confidence: {final_state.confidence_score}"
        )
        db.add(audit_end)
        db.commit()

    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED.value
            db.commit()
    finally:
        db.close()

@router.post("")
def create_task(req: TaskCreateRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    task = Task(
        title=req.title,
        description=req.description,
        project_id=req.project_id,
        status=TaskStatus.PENDING.value
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Launch in background
    bg.add_task(run_pipeline_task, task.id)

    return {
        "success": True,
        "task_id": task.id,
        "status": task.status,
        "message": "Task queued for autonomous execution."
    }

@router.get("")
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.id.desc()).all()
    return tasks

@router.get("/{task_id}")
def get_task_details(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "confidence_score": task.confidence_score,
        "current_agent": task.current_agent,
        "retry_count": task.retry_count,
        "created_at": task.created_at,
        "logs": task.logs,
        "test_results": task.test_results,
        "pull_requests": task.pull_requests,
        "docker_sessions": task.docker_sessions,
        "audit_logs": task.audit_logs,
        "notifications": task.notifications,
        "retry_history": task.retry_history
    }

@router.get("/{task_id}/files")
def get_task_files(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    workspace_dir = settings.SANDBOX_WORKSPACE_DIR / f"task_{task_id}"
    files = {}
    if workspace_dir.exists():
        for p in workspace_dir.rglob("*"):
            if p.is_file() and not any(part.startswith(".") for part in p.parts):
                rel = str(p.relative_to(workspace_dir)).replace("\\", "/")
                try:
                    files[rel] = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass
    return {"task_id": task_id, "files": files}

@router.get("/{task_id}/diff")
def get_task_diff(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    pr = db.query(PullRequest).filter(PullRequest.task_id == task_id).first()
    return {
        "task_id": task_id,
        "diff": pr.patch_diff if pr else "",
        "pr_url": pr.github_pr_url if pr else None,
        "pr_number": pr.pr_number if pr else None,
        "branch": pr.branch_name if pr else None,
        "status": pr.status if pr else "NONE"
    }

@router.post("/{task_id}/approve")
def human_approve_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.COMPLETED.value
    audit = AuditLog(
        task_id=task.id,
        action="HUMAN_OVERRIDE_APPROVE",
        actor="HumanDeveloper",
        payload="Human developer manually approved and resolved escalation."
    )
    db.add(audit)
    db.commit()
    return {"success": True, "task_id": task.id, "status": task.status}
