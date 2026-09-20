from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PipelineExecutionState(BaseModel):
    """
    Shared Pydantic state passed through the LangGraph multi-agent pipeline.
    """
    task_id: int = 0
    title: str = ""
    description: str = ""
    workspace_path: str = ""
    
    # Planner output
    plan: Dict[str, Any] = Field(default_factory=dict)
    
    # Coder output
    files: Dict[str, str] = Field(default_factory=dict)
    
    # Tester output
    test_files: Dict[str, str] = Field(default_factory=dict)
    test_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Critic output
    critic_review: Dict[str, Any] = Field(default_factory=dict)
    
    # Guardrail findings
    guardrail_violations: List[str] = Field(default_factory=list)
    guardrail_warnings: List[str] = Field(default_factory=list)
    
    # Execution metrics & metadata
    retry_count: int = 0
    confidence_score: float = 1.0
    current_agent: str = "Planner"
    status: str = "PENDING"
    is_escalated: bool = False
    escalation_reason: Optional[str] = None
    
    # GitHub PR & patch
    patch_diff: Optional[str] = None
    pr_info: Optional[Dict[str, Any]] = None
    
    # Telemetry and audit logs
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
