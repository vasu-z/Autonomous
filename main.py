import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import settings
from database.session import init_db
from orchestrator.state import PipelineExecutionState
from orchestrator.graph import DevOpsAgentOrchestrator

console = Console(legacy_windows=False)

def run_cli_pipeline(task_title: str, task_desc: str = ""):
    init_db()
    console.print(Panel(
        f"[bold cyan]AUTONOMOUS OPS/DEV AGENT WITH REAL GUARDRAILS[/bold cyan]\n"
        f"[dim]Self-Correcting Multi-Agent DevOps System[/dim]\n\n"
        f"[bold white]Task:[/bold white] {task_title}",
        border_style="cyan"
    ))

    workspace_dir = settings.SANDBOX_WORKSPACE_DIR / "cli_run"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    state = PipelineExecutionState(
        task_id=1,
        title=task_title,
        description=task_desc or task_title,
        workspace_path=str(workspace_dir.resolve())
    )

    orchestrator = DevOpsAgentOrchestrator()

    console.print("[cyan]> Executing Multi-Agent Pipeline (Planner -> Coder -> Guardrails -> Tester -> Critic)...[/cyan]")
    final_state = orchestrator.run(state)

    # Result Display
    status_color = "green" if final_state.status == "COMPLETED" else "red"
    console.print(Panel(
        f"[bold {status_color}]Pipeline Finished: {final_state.status}[/bold {status_color}]\n"
        f"Confidence Score: {final_state.confidence_score*100:.1f}%\n"
        f"Self-Correction Cycles: {final_state.retry_count}\n"
        f"Tokens: {final_state.tokens_in} in / {final_state.tokens_out} out\n"
        f"Generated Files: {list(final_state.files.keys())}\n"
        f"Test Result: {final_state.test_results.get('passed_count', 0)} passed, {final_state.test_results.get('failed_count', 0)} failed",
        title="Execution Summary",
        border_style=status_color
    ))

    if final_state.guardrail_violations:
        console.print(Panel(
            "\n".join(final_state.guardrail_violations),
            title="[bold red]Guardrail Violations Detected[/bold red]",
            border_style="red"
        ))

    if final_state.pr_info:
        console.print(f"[bold green][OK] Pull Request Ready:[/bold green] {final_state.pr_info.get('html_url')}")

def main():
    parser = argparse.ArgumentParser(description="Autonomous Ops/Dev Agent")
    parser.add_argument("task", nargs="?", help="Task description to execute")
    parser.add_argument("--server", action="store_true", help="Start the FastAPI control dashboard server")
    args = parser.parse_args()

    if args.server:
        import uvicorn
        console.print("[bold green]Starting Web Control Dashboard on http://localhost:8000[/bold green]")
        uvicorn.run("api.server:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
    elif args.task:
        run_cli_pipeline(args.task)
    else:
        # Default run demo task
        run_cli_pipeline(
            "Build a REST API for a todo app with FastAPI and SQLite",
            "Create FastAPI REST API with endpoints to create, read, update, delete todos. Include input sanitization and unit tests."
        )

if __name__ == "__main__":
    main()
