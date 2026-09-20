import json
from typing import Dict, Any
from agents.base import BaseAgent
from orchestrator.state import PipelineExecutionState

try:
    from external.multi_agent_coder.prompts.system_prompts import ARCHITECT_SYSTEM_PROMPT
except ImportError:
    ARCHITECT_SYSTEM_PROMPT = (
        "You are an expert Software Architect and DevOps Planner. "
        "Analyze the given issue or task description. Break it down into clear, structured subtasks, "
        "determine which files should be created or modified, and pick the optimal tech stack. "
        "Output your response strictly in valid JSON with keys: 'subtasks', 'files_to_create', 'tech_stack', 'approach'."
    )

class PlannerAgent(BaseAgent):
    """
    Planner Agent: Analyzes user requirements or GitHub issues,
    breaks them down into structured subtasks, and selects the architectural approach.
    """

    def __init__(self):
        super().__init__(name="Planner Agent", role="Software Architect & Planner")

    def plan(self, state: PipelineExecutionState) -> Dict[str, Any]:
        system_prompt = ARCHITECT_SYSTEM_PROMPT

        user_prompt = f"Task Title: {state.title}\nTask Description:\n{state.description}"
        result = self.generate(system_prompt, user_prompt)
        
        try:
            plan_data = json.loads(result["content"])
        except Exception:
            plan_data = {
                "subtasks": [f"Implement solution for: {state.title}"],
                "files_to_create": ["app/main.py"],
                "tech_stack": "Python 3.11",
                "approach": result["content"]
            }

        return {
            "plan": plan_data,
            "tokens_in": result["tokens_in"],
            "tokens_out": result["tokens_out"],
            "duration": result["duration"]
        }
