import re
from pathlib import Path
from typing import Dict, Any
from agents.base import BaseAgent
from orchestrator.state import PipelineExecutionState
from tools.file_tools import ACIFileTools
from tools.git_tools import ACIGitTools

# Direct import from external/multi_agent_coder
try:
    from external.multi_agent_coder.agents.coder import parse_file_tags
    from external.multi_agent_coder.prompts.system_prompts import CODER_SYSTEM_PROMPT, CODER_FIX_PROMPT
except ImportError:
    def parse_file_tags(text: str) -> Dict[str, str]:
        pattern = r'<file\s+path=["\']([^"\']+)["\']\s*>(.*?)</file>'
        matches = re.findall(pattern, text, re.DOTALL)
        files = {}
        for filepath, content in matches:
            files[filepath.strip()] = content.strip("\n")
        return files
    CODER_SYSTEM_PROMPT = "You are the Coder Agent."
    CODER_FIX_PROMPT = "Fix the issues described in the review feedback."

class CoderAgent(BaseAgent):
    """
    Coder Agent: Implements production software from the architectural plan,
    writes files safely using ACI tools, applies corrections from Critic feedback,
    and commits changes to the Git repository.
    """

    def __init__(self):
        super().__init__(name="Coder Agent", role="Software Implementation Engineer")

    def _parse_xml_files(self, text: str) -> Dict[str, str]:
        """Extracts files enclosed in <file name="...">...</file> blocks."""
        pattern = r'<file\s+name=["\']([^"\']+)["\']>(.*?)</file>'
        matches = re.findall(pattern, text, re.DOTALL)
        files = {}
        for filename, content in matches:
            files[filename.strip()] = content.strip()
        return files

    def code(self, state: PipelineExecutionState, workspace_path: Path) -> Dict[str, Any]:
        file_tools = ACIFileTools(workspace_path)
        git_tools = ACIGitTools(workspace_path)

        is_fix = state.retry_count > 0 and bool(state.critic_review.get("feedback"))
        system_prompt = CODER_FIX_PROMPT if is_fix else CODER_SYSTEM_PROMPT

        user_prompt = (
            f"Task: {state.title}\n"
            f"Description: {state.description}\n"
            f"Plan: {state.plan}\n"
        )

        if is_fix:
            user_prompt += (
                f"\n[CRITIC FEEDBACK - FIX REQUIRED (Cycle {state.retry_count})]:\n"
                f"{state.critic_review.get('feedback')}\n"
                f"Issues to resolve: {state.critic_review.get('issues', [])}\n"
            )

        result = self.generate(system_prompt, user_prompt)
        parsed_files = parse_file_tags(result["content"])

        if not parsed_files:
            # Check for <file name="..."> as well
            parsed_files = self._parse_xml_files(result["content"])

        if not parsed_files:
            # Fallback if no XML tags found
            parsed_files = {"app/main.py": result["content"]}

        # Write each file to workspace using ACI tools
        for rel_path, content in parsed_files.items():
            file_tools.write_file(rel_path, content)

        # Commit to git
        commit_msg = f"feat({state.title.lower()[:30]}): autonomous implementation"
        if state.retry_count > 0:
            commit_msg = f"fix: resolve critic feedback cycle {state.retry_count}"
        git_tools.commit_all(commit_msg)

        return {
            "files": parsed_files,
            "tokens_in": result["tokens_in"],
            "tokens_out": result["tokens_out"],
            "duration": result["duration"]
        }
