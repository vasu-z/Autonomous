from pathlib import Path
from typing import Dict, Any, List, Optional
import os
import re

class ACIFileTools:
    """
    Agent-Computer Interface (ACI) File Tools inspired by SWE-agent.
    Provides precise, structured file inspection, search, and editing.
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()

    def _resolve_safe(self, rel_path: str) -> Path:
        target = (self.workspace_root / rel_path).resolve()
        if not str(target).startswith(str(self.workspace_root)):
            raise ValueError(f"Path traversal attempted: {rel_path}")
        return target

    def view_file(self, rel_path: str, start_line: int = 1, end_line: int = -1) -> Dict[str, Any]:
        """Views file content with line numbers (1-indexed)."""
        target = self._resolve_safe(rel_path)
        if not target.exists() or not target.is_file():
            return {"success": False, "error": f"File not found: {rel_path}"}

        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        total_lines = len(lines)

        if end_line == -1 or end_line > total_lines:
            end_line = total_lines

        start_line = max(1, start_line)
        selected_lines = lines[start_line - 1 : end_line]
        
        numbered = [f"{start_line + i:4d} | {line}" for i, line in enumerate(selected_lines)]
        return {
            "success": True,
            "path": rel_path,
            "total_lines": total_lines,
            "start_line": start_line,
            "end_line": end_line,
            "content": "\n".join(numbered)
        }

    def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        """Creates or overwrites a file."""
        target = self._resolve_safe(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"success": True, "path": rel_path, "bytes_written": len(content)}

    def replace_lines(self, rel_path: str, target_string: str, replacement_string: str) -> Dict[str, Any]:
        """Replaces an exact code segment in a file (SWE-agent style)."""
        target = self._resolve_safe(rel_path)
        if not target.exists():
            return {"success": False, "error": f"File not found: {rel_path}"}

        content = target.read_text(encoding="utf-8")
        count = content.count(target_string)
        if count == 0:
            return {"success": False, "error": "Target string not found in file."}
        if count > 1:
            return {"success": False, "error": f"Target string appears {count} times. Replacement must be unique."}

        new_content = content.replace(target_string, replacement_string, 1)
        target.write_text(new_content, encoding="utf-8")
        return {"success": True, "path": rel_path, "replaced": True}

    def list_files(self) -> List[str]:
        """Lists all relative files in workspace."""
        files = []
        for p in self.workspace_root.rglob("*"):
            if p.is_file() and not any(part.startswith(".") for part in p.parts):
                files.append(str(p.relative_to(self.workspace_root)).replace("\\", "/"))
        return sorted(files)
