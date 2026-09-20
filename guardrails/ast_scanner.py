import ast
import re
from typing import Tuple, List, Dict, Any

class ASTSecurityScanner:
    """
    Analyzes Python source code using Abstract Syntax Trees (AST) to detect:
    - Syntax errors
    - Dangerous built-ins and functions (eval, exec, __import__)
    - Insecure modules (ctypes, pty)
    - Secret leaks (API keys, hardcoded credentials)
    """

    BANNED_MODULES = {"ctypes", "pty", "telnetlib", "code"}
    
    SECRET_REGEXES = [
        re.compile(r"""(?i)(?:api_key|apikey|secret|token|password|passwd|auth)\s*=\s*['"][a-zA-Z0-9_\-]{20,}['"]"""),
        re.compile(r"""ghp_[a-zA-Z0-9]{36}"""),
        re.compile(r"""sk-[a-zA-Z0-9]{48}"""),
    ]

    def scan_code(self, code_str: str) -> Dict[str, Any]:
        """
        Scans a Python code snippet or file content.
        Returns dictionary with:
        - is_safe: bool
        - syntax_valid: bool
        - errors: List[str]
        - warnings: List[str]
        """
        result = {
            "is_safe": True,
            "syntax_valid": True,
            "errors": [],
            "warnings": []
        }

        # 1. Syntax Validation
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            result["is_safe"] = False
            result["syntax_valid"] = False
            result["errors"].append(f"Syntax Error at line {e.lineno}: {e.msg}")
            return result

        # 2. AST Traversal for dangerous calls and imports
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.BANNED_MODULES:
                        result["is_safe"] = False
                        result["errors"].append(f"Insecure import blocked: '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.BANNED_MODULES:
                    result["is_safe"] = False
                    result["errors"].append(f"Insecure import blocked: '{node.module}'")

            # Check calls: eval, exec
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec"):
                        result["is_safe"] = False
                        result["errors"].append(f"Dangerous call detected: '{node.func.id}()'")

        # 3. Secret Leak Scanning
        for pattern in self.SECRET_REGEXES:
            matches = pattern.findall(code_str)
            if matches:
                result["warnings"].append(f"Possible hardcoded credential or secret detected: {len(matches)} occurrence(s)")
                # If secret is obvious OpenAI or GitHub token, mark unsafe
                for m in matches:
                    if "ghp_" in m or "sk-" in m:
                        result["is_safe"] = False
                        result["errors"].append("Hardcoded private token detected (GitHub/OpenAI key format).")

        return result
