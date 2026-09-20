from pathlib import Path
from typing import Union
from config import settings
from sandbox.docker_runner import DockerSandboxRunner
from sandbox.process_runner import ProcessSandboxRunner

def get_sandbox_runner(workspace_path: Path) -> Union[DockerSandboxRunner, ProcessSandboxRunner]:
    """
    Returns an active sandbox runner for the given workspace path.
    Prioritizes Docker if settings.USE_DOCKER is True and Docker daemon is running;
    otherwise seamlessly falls back to isolated ProcessSandboxRunner.
    """
    if settings.USE_DOCKER:
        docker_runner = DockerSandboxRunner(workspace_path=workspace_path)
        if docker_runner.is_docker_available():
            return docker_runner

    # Fallback to process runner
    return ProcessSandboxRunner(workspace_path=workspace_path)
