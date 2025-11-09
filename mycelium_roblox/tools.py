"""Collection of tool abstractions used by the Mycelium-Roblox agents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class ToolResult:
    success: bool
    details: str
    diagnostics: List[str]


class LocalLLM:
    """Minimal stand-in for a local LLaMA model.

    The implementation keeps things deterministic and offline by relying
    on heuristics instead of an actual model invocation. The class
    nonetheless mirrors the surface API expected by the agents so that a
    drop-in replacement with a true model would be straightforward.
    """

    def __init__(self, model_name: str, model_path: str, max_tokens: int) -> None:
        self.model_name = model_name
        self.model_path = Path(model_path)
        self.max_tokens = max_tokens

    def complete(self, prompt: str, temperature: float = 0.0) -> str:
        """Return a deterministic pseudo-completion.

        The behaviour is intentionally simple: the prompt is echoed back
        with a templated suffix. This keeps the system testable without a
        heavy model dependency, while providing a hook for future model
        integration.
        """

        summary = prompt.strip().split("\n")[-1][-self.max_tokens :]
        return f"[LLM:{self.model_name}] {summary}".strip()


class RobloxAPITool:
    """Stub accessor for Roblox API metadata."""

    def __init__(self, dump_path: str | Path) -> None:
        self.dump_path = Path(dump_path)

    def lookup(self, symbol: str) -> Dict[str, str]:
        # In a real setup this would parse the API dump. Here we provide a
        # minimal pretend response.
        return {
            "symbol": symbol,
            "description": "Stubbed Roblox API response; integrate with API dump for real usage.",
        }


class LuaLinter:
    """Performs lightweight lint checks on Lua code snippets."""

    def lint(self, code: str) -> ToolResult:
        diagnostics: List[str] = []
        success = True
        if "TODO" in code:
            diagnostics.append("Found unresolved TODO marker.")
            success = False
        if "print(" not in code:
            diagnostics.append("Suggestion: add trace logging with print() for visibility during development.")
        if "function" not in code:
            diagnostics.append("No Lua function detected; ensure behaviour is encapsulated in functions.")
        return ToolResult(success=success, details="Lint completed", diagnostics=diagnostics)


class LuaSandbox:
    """Simulated Lua execution environment.

    Real Roblox execution is not possible in this environment. Instead
    we mimic execution by parsing the Lua for a small set of heuristics
    and returning structured results that keep the learning loop moving.
    """

    def __init__(self, timeout_seconds: int = 5) -> None:
        self.timeout_seconds = timeout_seconds

    def run(self, code: str) -> ToolResult:
        diagnostics: List[str] = []
        success = True
        if "wait(" in code:
            diagnostics.append("Detected wait() usage; consider RunService.Heartbeat for smoother timing.")
        if "game:GetService" not in code:
            diagnostics.append("Script does not reference game services; verify dependencies.")
            success = False
        details = "Sandbox analysis complete"
        return ToolResult(success=success, details=details, diagnostics=diagnostics)


class LuaTestValidator:
    """Very small harness that fakes unit testing of Lua snippets."""

    def validate(self, code: str, expectations: Dict[str, str]) -> ToolResult:
        diagnostics: List[str] = []
        success = True
        for key, requirement in expectations.items():
            if requirement not in code:
                diagnostics.append(f"Missing required pattern '{requirement}' for expectation '{key}'.")
                success = False
        details = "Validation finished"
        return ToolResult(success=success, details=details, diagnostics=diagnostics)
