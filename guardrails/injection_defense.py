import re
from typing import Tuple, List

class PromptInjectionDefense:
    """
    Detects prompt injection attempts, system prompt overrides, and adversarial instructions
    inside user inputs, GitHub issues, and code comments.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)",
        r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|directives)",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"jailbreak\s+mode",
        r"do\s+anything\s+now",
        r"DAN\s+mode",
        r"system\s*:\s*override",
        r"bypass\s+(all\s+)?safety\s+(filters|guardrails)",
        r"act\s+as\s+an\s+unrestricted\s+ai",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[SYSTEM_PROMPT_OVERRIDE\]",
    ]

    def __init__(self, custom_patterns: List[str] = None):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        if custom_patterns:
            self.patterns.extend([re.compile(p, re.IGNORECASE) for p in custom_patterns])

    def inspect_text(self, text: str) -> Tuple[bool, float, str]:
        """
        Inspects text for prompt injection.
        Returns: (is_safe: bool, confidence_score: float, details: str)
        """
        if not text:
            return True, 1.0, "Empty text is considered safe."

        for pattern in self.patterns:
            match = pattern.search(text)
            if match:
                return (
                    False,
                    0.2,
                    f"Prompt injection detected matching pattern: '{match.group(0)}'"
                )

        # Baseline confidence score for clean input
        return True, 0.98, "No adversarial prompt injection patterns detected."
