import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class ACIGitTools:
    """
    Git tools for branch management, commit generation, diff computation, and patch export.
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()

    def _run_git(self, args: list) -> Dict[str, Any]:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                shell=True
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip()
            }
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}

    def init_if_needed(self) -> Dict[str, Any]:
        if not (self.workspace_root / ".git").exists():
            res = self._run_git(["init"])
            self._run_git(["config", "user.name", "Autonomous-OpsDev-Agent"])
            self._run_git(["config", "user.email", "agent@devops-guardrails.local"])
            return res
        return {"exit_code": 0, "stdout": "Git repository already initialized.", "stderr": ""}

    def create_branch(self, branch_name: str) -> Dict[str, Any]:
        self.init_if_needed()
        return self._run_git(["checkout", "-B", branch_name])

    def commit_all(self, message: str) -> Dict[str, Any]:
        self.init_if_needed()
        self._run_git(["add", "-A"])
        return self._run_git(["commit", "-m", message])

    def get_diff(self) -> str:
        self.init_if_needed()
        res = self._run_git(["diff", "HEAD~1", "HEAD"])
        if res["exit_code"] != 0 or not res["stdout"]:
            # fallback to git diff against empty or unstaged
            res = self._run_git(["diff"])
        return res["stdout"]

    def create_patch(self, output_patch_name: str = "changes.patch") -> Path:
        diff_text = self.get_diff()
        patch_path = self.workspace_root / output_patch_name
        patch_path.write_text(diff_text, encoding="utf-8")
        return patch_path
