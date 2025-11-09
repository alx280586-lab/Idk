"""Entry point tying together the Planner-Actor-Critic loop."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .actor import Actor
from .critic import Critic
from .memory import MemoryStore
from .planner import Planner
from .tools import LocalLLM, LuaLinter, LuaSandbox, LuaTestValidator, RobloxAPITool


def _parse_scalar(value: str) -> object:
    value = value.strip()
    if value == "" or value is None:
        return ""
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        pass
    for quote in ('"', "'"):
        if value.startswith(quote) and value.endswith(quote):
            return value[1:-1]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


def load_simple_yaml(path: str | Path) -> Dict[str, object]:
    text = Path(path).read_text(encoding="utf-8")
    root: Dict[str, object] = {}
    stack: list[tuple[int, Dict[str, object]]] = [(-1, root)]

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, _, value_part = raw_line.partition(":")
        key = key.strip()
        value_part = value_part.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if value_part == "":
            new_dict: Dict[str, object] = {}
            parent[key] = new_dict
            stack.append((indent, new_dict))
        else:
            parent[key] = _parse_scalar(value_part)
    return root


@dataclass
class Task:
    name: str
    description: str
    expectations: Dict[str, str]


class Runner:
    def __init__(self, config_path: str | Path = "config.yaml") -> None:
        self.config_path = Path(config_path)
        self.config = load_simple_yaml(self.config_path)
        self.memory = MemoryStore(self.config["memory"]["db_path"])

        llm_config = self.config["model"]
        self.llm = LocalLLM(
            model_name=str(llm_config.get("name", "llama")),
            model_path=str(llm_config.get("path", "./models")),
            max_tokens=int(llm_config.get("max_tokens", 256)),
        )

        tools_config = self.config.get("tools", {})
        self.api = RobloxAPITool(str(tools_config.get("roblox_api_dump", "./data/api.json")))
        self.linter = LuaLinter()
        self.sandbox = LuaSandbox(int(tools_config.get("sandbox_timeout", 5)))
        self.validator = LuaTestValidator()

        self.planner = Planner(self.llm, self.memory)
        self.actor = Actor(self.llm, self.memory)
        self.critic = Critic(self.linter, self.sandbox, self.validator)

    def run_task(self, task: Task) -> Dict[str, object]:
        task_id = self.memory.log_task(task.name, task.description)
        plan = self.planner.create_plan(task_id, task.description)
        actions = self.actor.execute_plan(plan.steps, task.description)

        combined_code = actions[-1].code if actions else ""
        critique = self.critic.review(combined_code, task.expectations)

        diagnostics = {
            "task_id": task_id,
            "plan": plan.steps,
            "actions": [action.notes for action in actions],
            "critic_success": critique.success,
            "critic_feedback": critique.step_feedback,
            "critic_diagnostics": critique.overall_diagnostics,
        }

        status = "success" if critique.success else "needs_revision"
        self.memory.log_result(task_id, status, json.dumps(diagnostics), combined_code)

        if not critique.success:
            self.memory.record_hard_case(task_id, "Critic reported failure; store for retraining.")

        return diagnostics

    def close(self) -> None:
        self.memory.close()


def main() -> None:
    runner = Runner()
    radar_task = Task(
        name="storm_radar_demo",
        description=(
            "Create a Roblox LocalScript that renders a 140x90 radar pixel grid "
            "showing a swirling storm pattern driven by Perlin noise, including "
            "random hesitation and RunService heartbeat updates."
        ),
        expectations={
            "uses_runservice": "RunService.Heartbeat:Connect",
            "uses_perlin": "math.noise",
            "grid_dimensions": "140",
        },
    )

    diagnostics = runner.run_task(radar_task)
    print("Task diagnostics:")
    print(json.dumps(diagnostics, indent=2))
    runner.close()


if __name__ == "__main__":
    main()
