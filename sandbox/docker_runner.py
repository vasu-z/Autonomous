import time
from pathlib import Path
from typing import Dict, Any, Optional
from config import settings

class DockerSandboxRunner:
    """
    Executes commands and tests inside an isolated Docker container,
    mounting the target workspace into /app.
    """

    def __init__(self, workspace_path: Path, image: str = None):
        self.workspace_path = workspace_path
        self.image = image or settings.DOCKER_IMAGE
        self.timeout = settings.SANDBOX_TIMEOUT_SECONDS
        self._client = None
        self._available = None

    def is_docker_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import docker
            self._client = docker.from_env()
            self._client.ping()
            self._available = True
        except Exception:
            self._available = False
        return self._available

    def run_command(self, command: str) -> Dict[str, Any]:
        """
        Runs a command inside a fresh Docker container with workspace mounted.
        """
        if not self.is_docker_available():
            raise RuntimeError("Docker daemon is not available or not running.")

        start_time = time.time()
        container = None
        try:
            # Create container with strict limits
            container = self._client.containers.create(
                image=self.image,
                command=["/bin/sh", "-c", command],
                working_dir="/workspace",
                volumes={
                    str(self.workspace_path.resolve()): {
                        "bind": "/workspace",
                        "mode": "rw"
                    }
                },
                network_mode="bridge",
                mem_limit="512m",
                nano_cpus=1000000000  # 1 CPU
            )

            container.start()
            container_id = container.id[:12]

            # Wait for exit or timeout
            poll_interval = 0.5
            waited = 0.0
            timed_out = False

            while waited < self.timeout:
                container.reload()
                if container.status == "exited":
                    break
                time.sleep(poll_interval)
                waited += poll_interval

            if container.status != "exited":
                container.kill()
                timed_out = True

            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            exit_code = -1 if timed_out else container.wait().get("StatusCode", 0)
            elapsed = time.time() - start_time

            return {
                "exit_code": exit_code,
                "stdout": logs if exit_code == 0 else "",
                "stderr": logs if exit_code != 0 else "",
                "execution_time": round(elapsed, 3),
                "timed_out": timed_out,
                "container_id": container_id,
                "runner_type": "docker_sandbox"
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Docker execution error: {str(e)}",
                "execution_time": round(elapsed, 3),
                "timed_out": False,
                "runner_type": "docker_sandbox"
            }
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
