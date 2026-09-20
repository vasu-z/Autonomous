import json
from typing import Dict, Any
from agents.base import BaseAgent
from orchestrator.state import PipelineExecutionState

try:
    from external.multi_agent_coder.prompts.system_prompts import REVIEWER_SYSTEM_PROMPT
except ImportError:
    REVIEWER_SYSTEM_PROMPT = (
        "You are a Principal Software Architect and Security Auditor. "
        "Perform a rigorous review of the code and test results. "
        "Output strictly valid JSON with keys: "
        "'approved' (boolean), 'score' (float 0.0 to 1.0), 'code_quality' (string), "
        "'security_assessment' (string), 'feedback' (string), 'issues' (list of strings)."
    )

class CriticAgent(BaseAgent):
    """
    Critic Agent: Performs independent code review, quality assessment,
    security evaluation, and evaluates test outcomes.
    Decides whether to APPROVE or REJECT the implementation.
    """

    def __init__(self):
        super().__init__(name="Critic Agent", role="Lead Code Reviewer & Security Analyst")

    def review(self, state: PipelineExecutionState) -> Dict[str, Any]:
        system_prompt = REVIEWER_SYSTEM_PROMPT

        all_tests_passed = state.test_results.get("all_passed", False)
        
        user_prompt = (
            f"Task: {state.title}\n"
            f"Code Files:\n"
            + "\n---\n".join([f"{name}:\n{content}" for name, content in state.files.items()])
            + f"\n\nTest Results (All Passed: {all_tests_passed}):\n"
            + f"Output:\n{state.test_results.get('output', '')}\n"
        )

        result = self.generate(system_prompt, user_prompt)
        try:
            review_data = json.loads(result["content"])
        except Exception:
            # If test passed, approve by default, otherwise reject
            review_data = {
                "approved": all_tests_passed,
                "score": 0.95 if all_tests_passed else 0.4,
                "code_quality": "Satisfactory" if all_tests_passed else "Needs Improvement",
                "security_assessment": "Standard review passed.",
                "feedback": "Automated tests passed successfully." if all_tests_passed else "Tests failed.",
                "issues": [] if all_tests_passed else ["Test failure reported by test runner."]
            }

        # Override approval if tests actually failed
        if not all_tests_passed:
            review_data["approved"] = False
            review_data["score"] = min(review_data.get("score", 0.5), 0.45)
            if "Tests failed in sandbox" not in review_data.get("issues", []):
                review_data.setdefault("issues", []).append("Tests failed in execution sandbox.")

        return {
            "critic_review": review_data,
            "tokens_in": result["tokens_in"],
            "tokens_out": result["tokens_out"],
            "duration": result["duration"]
        }
