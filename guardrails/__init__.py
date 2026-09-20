from typing import Dict, Any, List, Optional
from guardrails.firewall import CommandFirewall
from guardrails.injection_defense import PromptInjectionDefense
from guardrails.ast_scanner import ASTSecurityScanner
from config import settings

class GuardrailDecision:
    def __init__(self, passed: bool, confidence_score: float, violations: List[str], warnings: List[str]):
        self.passed = passed
        self.confidence_score = confidence_score
        self.violations = violations
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "confidence_score": self.confidence_score,
            "violations": self.violations,
            "warnings": self.warnings,
        }

class GuardrailEngine:
    """
    Unified Guardrail Engine:
    - Defense against prompt injections in tasks/issues
    - Interception of dangerous shell commands
    - Static AST validation of generated Python code
    - Dynamic confidence scoring and escalation triggers
    """

    def __init__(self):
        self.firewall = CommandFirewall()
        self.injection_defense = PromptInjectionDefense()
        self.ast_scanner = ASTSecurityScanner()
        self.confidence_threshold = settings.GUARDRAIL_CONFIDENCE_THRESHOLD

    def validate_task_input(self, task_description: str) -> GuardrailDecision:
        """Inspects incoming user prompt or GitHub issue for prompt injections."""
        is_safe, confidence, details = self.injection_defense.inspect_text(task_description)
        violations = [] if is_safe else [details]
        return GuardrailDecision(
            passed=is_safe and (confidence >= self.confidence_threshold),
            confidence_score=confidence,
            violations=violations,
            warnings=[]
        )

    def validate_command(self, command: str) -> GuardrailDecision:
        """Inspects a shell command before execution."""
        is_allowed, reason = self.firewall.validate_command(command)
        violations = [] if is_allowed else [reason]
        score = 1.0 if is_allowed else 0.0
        return GuardrailDecision(
            passed=is_allowed,
            confidence_score=score,
            violations=violations,
            warnings=[]
        )

    def validate_code(self, filename: str, code_content: str) -> GuardrailDecision:
        """Inspects generated code files for syntax errors, dangerous calls, and secret leaks."""
        if not filename.endswith(".py"):
            return GuardrailDecision(passed=True, confidence_score=1.0, violations=[], warnings=[])

        scan_res = self.ast_scanner.scan_code(code_content)
        confidence = 1.0
        if scan_res["warnings"]:
            confidence -= 0.15 * len(scan_res["warnings"])
        if not scan_res["is_safe"]:
            confidence = 0.3

        confidence = max(0.0, min(1.0, confidence))
        passed = scan_res["is_safe"] and (confidence >= self.confidence_threshold)

        return GuardrailDecision(
            passed=passed,
            confidence_score=confidence,
            violations=scan_res["errors"],
            warnings=scan_res["warnings"]
        )

# Global singleton
guardrail_engine = GuardrailEngine()
