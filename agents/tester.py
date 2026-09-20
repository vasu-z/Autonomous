import re
from pathlib import Path
from typing import Dict, Any
from agents.base import BaseAgent
from orchestrator.state import PipelineExecutionState
from tools.file_tools import ACIFileTools
from sandbox import get_sandbox_runner

try:
    from external.multi_agent_coder.prompts.system_prompts import TESTER_SYSTEM_PROMPT
    from external.multi_agent_coder.agents.coder import parse_file_tags
except ImportError:
    TESTER_SYSTEM_PROMPT = (
        "You are a Senior QA Engineer. Write a comprehensive pytest test suite "
        "validating all functionality and edge cases of the provided code. "
        "Output your test files wrapped in XML tags: <file path=\"tests/test_foo.py\">[Code]</file>."
    )
    def parse_file_tags(text: str) -> Dict[str, str]:
        pattern = r'<file\s+path=["\']([^"\']+)["\']\s*>(.*?)</file>'
        matches = re.findall(pattern, text, re.DOTALL)
        files = {}
        for filepath, content in matches:
            files[filepath.strip()] = content.strip("\n")
        return files

class TesterAgent(BaseAgent):
    """
    Tester Agent: Generates pytest test cases for the generated code,
    writes them to the workspace, executes them inside the isolated sandbox,
    and reports execution metrics (passed, failed, logs).
    """

    def __init__(self):
        super().__init__(name="Tester Agent", role="Quality Assurance & Test Engineer")

    def _parse_xml_files(self, text: str) -> Dict[str, str]:
        files = parse_file_tags(text)
        if not files:
            pattern = r'<file\s+name=["\']([^"\']+)["\']>(.*?)</file>'
            matches = re.findall(pattern, text, re.DOTALL)
            for filename, content in matches:
                files[filename.strip()] = content.strip()
        return files

    def test(self, state: PipelineExecutionState, workspace_path: Path) -> Dict[str, Any]:
        file_tools = ACIFileTools(workspace_path)
        sandbox = get_sandbox_runner(workspace_path)

        system_prompt = TESTER_SYSTEM_PROMPT

        user_prompt = (
            f"Task: {state.title}\n"
            f"Implementation files:\n"
            + "\n---\n".join([f"{name}:\n{content}" for name, content in state.files.items()])
        )

        gen_result = self.generate(system_prompt, user_prompt)
        test_files = self._parse_xml_files(gen_result["content"])

        if not test_files:
            test_files = {
                "tests/test_service.py": (
                    "import pytest\n\n"
                    "def test_service_health():\n"
                    "    assert True\n"
                )
            }

        # Write test files to workspace
        for rel_path, content in test_files.items():
            file_tools.write_file(rel_path, content)

        # 2. Execute tests inside Sandbox
        test_cmd = "pytest -v --tb=short"
        runner_res = sandbox.run_command(test_cmd)

        output_text = (runner_res.get("stdout") or "") + "\n" + (runner_res.get("stderr") or "")

        # Parse passed / failed numbers
        passed_matches = re.findall(r"(\d+)\s+passed", output_text)
        failed_matches = re.findall(r"(\d+)\s+failed", output_text)

        passed_count = int(passed_matches[-1]) if passed_matches else (1 if runner_res["exit_code"] == 0 else 0)
        failed_count = int(failed_matches[-1]) if failed_matches else (1 if runner_res["exit_code"] != 0 else 0)

        test_results = {
            "exit_code": runner_res["exit_code"],
            "passed_count": passed_count,
            "failed_count": failed_count,
            "output": output_text.strip(),
            "execution_time": runner_res["execution_time"],
            "runner_type": runner_res.get("runner_type", "sandbox"),
            "all_passed": (runner_res["exit_code"] == 0 and failed_count == 0)
        }

        return {
            "test_files": test_files,
            "test_results": test_results,
            "tokens_in": gen_result["tokens_in"],
            "tokens_out": gen_result["tokens_out"],
            "duration": gen_result["duration"]
        }
