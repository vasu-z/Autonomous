import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseModel):
    # App
    APP_NAME: str = "Autonomous Ops/Dev Agent with Real Guardrails"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Security & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-jwt-devops-guardrails-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'devops_agent.db'}")
    
    # Docker & Sandbox
    USE_DOCKER: bool = os.getenv("USE_DOCKER", "true").lower() in ("true", "1", "yes")
    DOCKER_IMAGE: str = os.getenv("DOCKER_IMAGE", "python:3.11-slim")
    SANDBOX_TIMEOUT_SECONDS: int = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "60"))
    SANDBOX_WORKSPACE_DIR: Path = BASE_DIR / "workspace_runs"
    
    # Guardrails
    GUARDRAIL_CONFIDENCE_THRESHOLD: float = float(os.getenv("GUARDRAIL_CONFIDENCE_THRESHOLD", "0.75"))
    MAX_RETRY_CYCLES: int = int(os.getenv("MAX_RETRY_CYCLES", "2"))
    BLOCK_DANGEROUS_COMMANDS: bool = True
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # mock | openai | anthropic | gemini | ollama | groq
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    
    # GitHub Integration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_DEFAULT_REPO: str = os.getenv("GITHUB_DEFAULT_REPO", "")

settings = Settings()

# Ensure directories exist
settings.SANDBOX_WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
