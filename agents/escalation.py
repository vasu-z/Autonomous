from typing import Dict, Any
from agents.base import BaseAgent
from orchestrator.state import PipelineExecutionState
from config import settings

class EscalationAgent(BaseAgent):
    """
    Escalation Agent: The final safety barrier. Intervenes whenever confidence scores
    fall below threshold, repeated retry cycles fail, or critical guardrails are violated.
    Prevents deploying defective software and issues an alert for human review.
    """

    def __init__(self):
        super().__init__(name="Escalation Agent", role="Safety Officer & Human Escalation Arbiter")

    def evaluate(self, state: PipelineExecutionState) -> Dict[str, Any]:
        should_escalate = False
        reasons = []

        # 1. Check confidence threshold
        if state.confidence_score < settings.GUARDRAIL_CONFIDENCE_THRESHOLD:
            should_escalate = True
            reasons.append(
                f"Confidence score ({state.confidence_score:.2f}) is below threshold ({settings.GUARDRAIL_CONFIDENCE_THRESHOLD:.2f})."
            )

        # 2. Check retry cycles
        if state.retry_count >= settings.MAX_RETRY_CYCLES and not state.critic_review.get("approved", False):
            should_escalate = True
            reasons.append(
                f"Maximum self-correction cycles ({settings.MAX_RETRY_CYCLES}) exceeded without Critic approval."
            )

        # 3. Check guardrail violations
        if state.guardrail_violations:
            should_escalate = True
            reasons.append(f"Critical guardrail violations detected: {', '.join(state.guardrail_violations)}")

        escalation_report = {
            "escalated": should_escalate,
            "reasons": reasons,
            "severity": "CRITICAL" if should_escalate else "NORMAL",
            "recommended_action": "Pause pipeline, notify human developer via dashboard, require manual override." if should_escalate else "Proceed normally."
        }

        return {
            "is_escalated": should_escalate,
            "escalation_reason": " | ".join(reasons) if reasons else None,
            "escalation_report": escalation_report
        }
