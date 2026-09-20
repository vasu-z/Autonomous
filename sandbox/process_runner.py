import subprocess
import os
import time
from pathlib import Path
from typing import Dict, Any
from config import settings

class ProcessSandboxRunner:
    """
    Isolated Subprocess execution environment.
    Runs commands within a specific workspace directory, with strict timeouts and environment isolation.
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.timeout = settings.SANDBOX_TIMEOUT_SECONDS

    def run_command(self, command: str, env_vars: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Executes a shell command in the confined workspace directory.
        """
        start_time = time.time()
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        ws_str = str(self.workspace_path.resolve())
        env["PYTHONPATH"] = f"{ws_str}{os.pathsep}{current_pythonpath}" if current_pythonpath else ws_str
        if env_vars:
            env.update(env_vars)

        try:
            # Run command synchronously with timeout
            process = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env
            )
            elapsed = time.time() - start_time
            return {
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "execution_time": round(elapsed, 3),
                "timed_out": False,
                "runner_type": "process_sandbox"
            }
        except subprocess.TimeoutExpired as te:
            elapsed = time.time() - start_time
            return {
                "exit_code": -1,
                "stdout": te.stdout or "",
                "stderr": f"Execution timed out after {self.timeout} seconds.",
                "execution_time": round(elapsed, 3),
                "timed_out": True,
                "runner_type": "process_sandbox"
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution failed with error: {str(e)}",
                "execution_time": round(elapsed, 3),
                "timed_out": False,
                "runner_type": "process_sandbox"
            }
