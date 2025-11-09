"""Critic agent responsible for validating generated Lua code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .tools import LuaLinter, LuaSandbox, LuaTestValidator, ToolResult


@dataclass
class Critique:
    success: bool
    step_feedback: List[str]
    overall_diagnostics: List[str]


class Critic:
    """Coordinates linting, sandbox analysis, and validation checks."""

    def __init__(self, linter: LuaLinter, sandbox: LuaSandbox, validator: LuaTestValidator) -> None:
        self.linter = linter
        self.sandbox = sandbox
        self.validator = validator

    def review(self, code: str, expectations: Dict[str, str]) -> Critique:
        lint_result = self.linter.lint(code)
        sandbox_result = self.sandbox.run(code)
        validation_result = self.validator.validate(code, expectations)

        diagnostics: List[str] = []
        step_feedback: List[str] = []

        for result in (lint_result, sandbox_result, validation_result):
            prefix = result.details
            for message in result.diagnostics:
                step_feedback.append(f"{prefix}: {message}")
            diagnostics.append(f"{prefix}: {'PASS' if result.success else 'FAIL'}")

        success = all(result.success for result in (lint_result, sandbox_result, validation_result))
        return Critique(success=success, step_feedback=step_feedback, overall_diagnostics=diagnostics)
