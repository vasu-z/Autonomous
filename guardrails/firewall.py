import re
from typing import Tuple, List

class CommandFirewall:
    """
    Validates shell commands before execution in the sandbox or local environment.
    Blocks dangerous, destructive, or exfiltration commands.
    """
    
    BANNED_PATTERNS = [
        # Destructive file deletions
        r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-f?[a-zA-Z]*r[a-zA-Z]*)\s+([~/]|\*|\.\.?)\b",
        r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-f?[a-zA-Z]*r[a-zA-Z]*)\s+\.",
        r"\brm\s+-rf\s+/",
        r"\bmkfs\b",
        r"\bformat\s+[a-zA-Z]:",
        # Dangerous disk writes
        r"\bdd\s+if=.*of=/dev/(sd|hd|nvme)",
        # Fork bombs
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",
        # Pipe to shell from remote
        r"\b(curl|wget)\b.*\|\s*(bash|sh|zsh|powershell|cmd)",
        # Reverse shells
        r"\b(nc|netcat|ncat)\b.*-e\s+(/bin/sh|/bin/bash|cmd\.exe|powershell)",
        r"/dev/tcp/\d+\.\d+\.\d+\.\d+/\d+",
        # Unauthorized privilege escalation
        r"\bchmod\s+777\s+/",
        r"\bchown\s+-R\s+root\s+/",
        # Dangerous windows commands
        r"\bdel\s+/[sS]\s+/[qQ]\s+[cC]:\\",
        r"\bshutdown\s+/[sSrR]",
    ]

    def __init__(self, custom_banned_patterns: List[str] = None):
        self.banned_regexes = [
            re.compile(p, re.IGNORECASE) for p in self.BANNED_PATTERNS
        ]
        if custom_banned_patterns:
            self.banned_regexes.extend([
                re.compile(p, re.IGNORECASE) for p in custom_banned_patterns
            ])

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validates a command.
        Returns: (is_allowed: bool, reason: str)
        """
        if not command or not command.strip():
            return False, "Empty command provided."
            
        cmd_clean = command.strip()

        for pattern in self.banned_regexes:
            if pattern.search(cmd_clean):
                return False, f"Blocked by Command Firewall: command matches forbidden security policy '{pattern.pattern}'"

        return True, "Command passed security checks."
