import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.session import Base
from database.models import (
    User, Project, Task, AgentLog, TestResult, PullRequest,
    DockerSession, AuditLog, Notification, RetryHistory,
    TaskStatus, UserRole
)

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_all_ten_tables_crud(db_session):
    # 1. User
    user = User(username="vasu", email="vasu@example.com", hashed_password="fakehash", role=UserRole.ADMIN.value)
    db_session.add(user)
    db_session.commit()
    assert user.id is not None

    # 2. Project
    project = Project(name="DevOps-Platform", repo_url="https://github.com/mmec/devops", user_id=user.id)
    db_session.add(project)
    db_session.commit()
    assert project.id is not None

    # 3. Task
    task = Task(title="Test Task", description="Implement auth", project_id=project.id, status=TaskStatus.RUNNING.value)
    db_session.add(task)
    db_session.commit()
    assert task.id is not None

    # 4. AgentLog
    log = AgentLog(task_id=task.id, agent_name="Planner", message="Planning subtasks...")
    db_session.add(log)

    # 5. TestResult
    tr = TestResult(task_id=task.id, passed_count=5, failed_count=0, test_output="5 passed")
    db_session.add(tr)

    # 6. PullRequest
    pr = PullRequest(task_id=task.id, github_pr_url="https://github.com/mmec/devops/pull/1", branch_name="fix/auth")
    db_session.add(pr)

    # 7. DockerSession
    ds = DockerSession(task_id=task.id, container_id="c12345", status="RUNNING", cpu_usage=12.5, memory_usage=128.0)
    db_session.add(ds)

    # 8. AuditLog
    audit = AuditLog(task_id=task.id, action="TASK_EXECUTE", actor="CoderAgent", payload="Wrote main.py")
    db_session.add(audit)

    # 9. Notification
    notif = Notification(task_id=task.id, type="INFO", message="Task started successfully")
    db_session.add(notif)

    # 10. RetryHistory
    retry = RetryHistory(task_id=task.id, cycle_number=1, critic_feedback="Add docstring")
    db_session.add(retry)

    db_session.commit()

    # Verify associations
    task_retrieved = db_session.query(Task).filter(Task.id == task.id).first()
    assert len(task_retrieved.logs) == 1
    assert len(task_retrieved.test_results) == 1
    assert len(task_retrieved.pull_requests) == 1
    assert len(task_retrieved.docker_sessions) == 1
    assert len(task_retrieved.audit_logs) == 1
    assert len(task_retrieved.notifications) == 1
    assert len(task_retrieved.retry_history) == 1
