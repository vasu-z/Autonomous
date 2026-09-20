import os
import time
from pathlib import Path
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from orchestrator.state import PipelineExecutionState
from agents.planner import PlannerAgent
from agents.coder import CoderAgent
from agents.tester import TesterAgent
from agents.critic import CriticAgent
from agents.escalation import EscalationAgent
from guardrails import guardrail_engine
from tools.git_tools import ACIGitTools
from integrations.github_client import GitHubClient
from config import settings

class DevOpsAgentOrchestrator:
    """
    Orchestrates the multi-agent DevOps workflow using LangGraph state machine.
    Enforces the self-correction loop, live guardrails, and escalation thresholds.
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.tester = TesterAgent()
        self.critic = CriticAgent()
        self.escalation = EscalationAgent()
        self.github_client = GitHubClient()
        self.graph = self._build_graph()

    def _planner_node(self, state: PipelineExecutionState) -> Dict[str, Any]:
        state.current_agent = "Planner"
        state.status = "PLANNING"
        
        # Guardrail check on input
        input_decision = guardrail_engine.validate_task_input(state.description)
        if not input_decision.passed:
            return {
                "guardrail_violations": input_decision.violations,
                "confidence_score": input_decision.confidence_score,
                "is_escalated": True,
                "escalation_reason": f"Input Guardrail Violation: {input_decision.violations}",
                "status": "ESCALATED"
            }

        res = self.planner.plan(state)
        return {
            "plan": res["plan"],
            "tokens_in": state.tokens_in + res["tokens_in"],
            "tokens_out": state.tokens_out + res["tokens_out"],
            "status": "CODING"
        }

    def _coder_node(self, state: PipelineExecutionState) -> Dict[str, Any]:
        state.current_agent = "Coder"
        workspace_path = Path(state.workspace_path)
        
        retry_inc = 1 if state.critic_review else 0
        current_retries = state.retry_count + retry_inc

        res = self.coder.code(state, workspace_path)
        
        # Run Guardrails on generated files
        violations = []
        warnings = []
        for filename, code in res["files"].items():
            guard_res = guardrail_engine.validate_code(filename, code)
            if not guard_res.passed:
                violations.extend(guard_res.violations)
            warnings.extend(guard_res.warnings)

        return {
            "files": res["files"],
            "guardrail_violations": violations,
            "guardrail_warnings": warnings,
            "retry_count": current_retries,
            "tokens_in": state.tokens_in + res["tokens_in"],
            "tokens_out": state.tokens_out + res["tokens_out"],
            "status": "TESTING"
        }

    def _tester_node(self, state: PipelineExecutionState) -> Dict[str, Any]:
        state.current_agent = "Tester"
        workspace_path = Path(state.workspace_path)

        res = self.tester.test(state, workspace_path)
        return {
            "test_files": res["test_files"],
            "test_results": res["test_results"],
            "tokens_in": state.tokens_in + res["tokens_in"],
            "tokens_out": state.tokens_out + res["tokens_out"],
            "status": "REVIEWING"
        }

    def _critic_node(self, state: PipelineExecutionState) -> Dict[str, Any]:
        state.current_agent = "Critic"
        res = self.critic.review(state)
        
        # Calculate dynamic confidence
        score = res["critic_review"].get("score", 0.5)
        if state.guardrail_violations:
            score -= 0.3
        score = max(0.0, min(1.0, score))

        return {
            "critic_review": res["critic_review"],
            "confidence_score": score,
            "tokens_in": state.tokens_in + res["tokens_in"],
            "tokens_out": state.tokens_out + res["tokens_out"],
            "status": "EVALUATING"
        }

    def _escalation_node(self, state: PipelineExecutionState) -> Dict[str, Any]:
        state.current_agent = "Escalation"
        res = self.escalation.evaluate(state)
        return {
            "is_escalated": True,
            "escalation_reason": res["escalation_reason"],
            "status": "ESCALATED"
        }

    def _finalize_node(self, state: PipelineExecutionState) -> Dict[str, Any]:
        workspace_path = Path(state.workspace_path)
        git_tools = ACIGitTools(workspace_path)

        # Generate patch
        patch_path = git_tools.create_patch()
        patch_diff = patch_path.read_text(encoding="utf-8") if patch_path.exists() else ""

        # Create simulated or real PR
        branch_name = f"devops-fix/task-{state.task_id}"
        pr_result = self.github_client.create_pull_request(
            repo=settings.GITHUB_DEFAULT_REPO,
            branch=branch_name,
            base="main",
            title=f"Autonomous fix for: {state.title}",
            body=f"Automated PR created by Autonomous Ops/Dev Agent.\n\nConfidence: {state.confidence_score*100:.1f}%\nTests passed: {state.test_results.get('passed_count', 0)}"
        )

        return {
            "patch_diff": patch_diff,
            "pr_info": pr_result,
            "status": "COMPLETED"
        }

    def _decide_after_planner(self, state: PipelineExecutionState) -> Literal["coder", "escalation"]:
        if state.is_escalated or state.guardrail_violations:
            return "escalation"
        return "coder"

    def _decide_after_critic(self, state: PipelineExecutionState) -> Literal["finalize", "coder", "escalation"]:
        if state.is_escalated or state.guardrail_violations:
            return "escalation"

        approved = state.critic_review.get("approved", False)
        if approved:
            return "finalize"
        
        if state.retry_count < settings.MAX_RETRY_CYCLES:
            return "coder"
        else:
            return "escalation"

    def _build_graph(self):
        workflow = StateGraph(PipelineExecutionState)

        workflow.add_node("planner", self._planner_node)
        workflow.add_node("coder", self._coder_node)
        workflow.add_node("tester", self._tester_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("escalation", self._escalation_node)
        workflow.add_node("finalize", self._finalize_node)

        # Edges
        workflow.set_entry_point("planner")
        workflow.add_conditional_edges(
            "planner",
            self._decide_after_planner,
            {
                "coder": "coder",
                "escalation": "escalation"
            }
        )
        workflow.add_edge("coder", "tester")
        workflow.add_edge("tester", "critic")

        # Conditional branch from Critic
        workflow.add_conditional_edges(
            "critic",
            self._decide_after_critic,
            {
                "finalize": "finalize",
                "coder": "coder",
                "escalation": "escalation"
            }
        )

        workflow.add_edge("finalize", END)
        workflow.add_edge("escalation", END)

        return workflow.compile()

    def run(self, initial_state: PipelineExecutionState) -> PipelineExecutionState:
        result = self.graph.invoke(initial_state)
        if isinstance(result, dict):
            return PipelineExecutionState(**result)
        return result
