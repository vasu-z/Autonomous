import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database.session import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"

class GuardrailStatus(str, enum.Enum):
    PASSED = "PASSED"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"

class NotificationType(str, enum.Enum):
    ESCALATION = "ESCALATION"
    APPROVAL = "APPROVAL"
    WARNING = "WARNING"
    INFO = "INFO"

# 1. Users Table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.DEVELOPER.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    projects = relationship("Project", back_populates="owner")

# 2. Projects Table
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    repo_url = Column(String(500), nullable=True)
    default_branch = Column(String(100), default="main")
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")

# 3. Tasks Table
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default=TaskStatus.PENDING.value)
    confidence_score = Column(Float, default=1.0)
    current_agent = Column(String(100), default="Planner")
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    logs = relationship("AgentLog", back_populates="task", cascade="all, delete-orphan")
    test_results = relationship("TestResult", back_populates="task", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="task", cascade="all, delete-orphan")
    docker_sessions = relationship("DockerSession", back_populates="task", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="task", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="task", cascade="all, delete-orphan")
    retry_history = relationship("RetryHistory", back_populates="task", cascade="all, delete-orphan")

# 4. Agent Logs Table
class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    level = Column(String(50), default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="logs")

# 5. Test Results Table
class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    test_output = Column(Text, nullable=True)
    coverage = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="test_results")

# 6. Pull Requests Table
class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    github_pr_url = Column(String(500), nullable=True)
    pr_number = Column(Integer, nullable=True)
    branch_name = Column(String(200), nullable=False)
    status = Column(String(50), default="OPEN")
    patch_diff = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="pull_requests")

# 7. Docker Sessions Table
class DockerSession(Base):
    __tablename__ = "docker_sessions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    container_id = Column(String(120), nullable=True)
    status = Column(String(50), default="INIT")
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="docker_sessions")

# 8. Audit Logs Table
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    action = Column(String(200), nullable=False)
    actor = Column(String(100), nullable=False)
    guardrail_status = Column(String(50), default=GuardrailStatus.PASSED.value)
    payload = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="audit_logs")

# 9. Notifications Table
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    recipient = Column(String(255), nullable=True)
    type = Column(String(50), default=NotificationType.INFO.value)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="notifications")

# 10. Retry History Table
class RetryHistory(Base):
    __tablename__ = "retry_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    critic_feedback = Column(Text, nullable=False)
    coder_changes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="retry_history")
