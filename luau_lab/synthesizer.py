"""Simplified Luau code synthesizer and explainer."""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SynthesisRequest:
    raw_text: str
    intent: str
    tag: Optional[str] = None
    service: Optional[str] = None


class LuauSynthesizer:
    """Create Luau scripts using templates and heuristics."""

    def __init__(self, heuristics: Dict[str, Dict[str, object]]) -> None:
        self.heuristics = heuristics
        self.random = random.Random()

    def update_seed(self, seed: Optional[int]) -> None:
        if seed is not None:
            self.random.seed(seed)

    def infer_request(self, prompt: str) -> SynthesisRequest:
        lowered = prompt.lower()
        if "spawn" in lowered:
            tag_match = re.search(r"tag(?:ged)?\s+'?([a-zA-Z0-9_]+)'?", lowered)
            tag = tag_match.group(1) if tag_match else "Spawn"
            return SynthesisRequest(raw_text=prompt, intent="spawn", tag=tag)
        if "teleport" in lowered:
            return SynthesisRequest(raw_text=prompt, intent="teleport")
        if "storm" in lowered or "radar" in lowered:
            return SynthesisRequest(raw_text=prompt, intent="storm")
        return SynthesisRequest(raw_text=prompt, intent="generic")

    def generate(self, prompt: str) -> str:
        request = self.infer_request(prompt)
        intent = request.intent
        if intent == "spawn":
            return self._spawn_template(request)
        if intent == "teleport":
            return self._teleport_template()
        if intent == "storm":
            return self._storm_template()
        return self._generic_template()

    def explain(self, code: str) -> List[str]:
        explanation: List[str] = []
        for idx, line in enumerate(code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("local CollectionService"):
                explanation.append(
                    f"Line {idx}: Acquire CollectionService so we can query tagged instances."
                )
            elif "GetTagged" in stripped:
                explanation.append(
                    f"Line {idx}: Collect only parts tagged with the requested label."
                )
            elif "math.random" in stripped or "Random.new" in stripped:
                explanation.append(
                    f"Line {idx}: Choose a random spawn to avoid clustering."
                )
            elif "Position" in stripped:
                explanation.append(
                    f"Line {idx}: Return a Vector3 position for the caller to use."
                )
            elif stripped.startswith("return"):
                explanation.append(f"Line {idx}: Expose the main function to other scripts.")
            else:
                explanation.append(f"Line {idx}: {stripped}")
        return explanation

    # Template helpers -------------------------------------------------

    def _spawn_template(self, request: SynthesisRequest) -> str:
        prefer_random_new = self.heuristics.get("preferences", {}).get("prefer_random_new", False)
        function_name = self._format_name("pickRandomSpawn", kind="function")
        tag_parameter = request.tag or "NPC"
        rng_line = (
            "    local rng = Random.new()\n"
            "    local choice = spawns[rng:NextInteger(1, #spawns)]"
        ) if prefer_random_new else (
            "    local choice = spawns[math.random(1, #spawns)]"
        )

        lines = [
            "local CollectionService = game:GetService(\"CollectionService\")",
            "",
            f"local function {function_name}(spawnTag)",
            "    local spawns = CollectionService:GetTagged(spawnTag or \"%s\")" % tag_parameter,
            "    if #spawns == 0 then",
            "        return nil",
            "    end",
            rng_line,
            "    return choice.Position",
            "end",
            "",
            "return %s" % function_name,
        ]
        return "\n".join(lines)

    def _teleport_template(self) -> str:
        lines = [
            "local Players = game:GetService(\"Players\")",
            "",
            "local function teleportPlayer(player, destination)",
            "    assert(player and destination, \"Missing player or destination\")",
            "    if player.Character and player.Character:FindFirstChild(\"HumanoidRootPart\") then",
            "        player.Character.HumanoidRootPart.CFrame = destination.CFrame",
            "    end",
            "end",
            "",
            "return teleportPlayer",
        ]
        return "\n".join(lines)

    def _storm_template(self) -> str:
        lines = [
            "local RunService = game:GetService(\"RunService\")",
            "local Workspace = game:GetService(\"Workspace\")",
            "",
            "local function startStorm(pixelFolder, duration)",
            "    local elapsed = 0",
            "    local connection",
            "    connection = RunService.Heartbeat:Connect(function(dt)",
            "        elapsed += dt",
            "        for _, pixel in ipairs(pixelFolder:GetChildren()) do",
            "            pixel.Color = Color3.fromHSV((elapsed + pixel.LayoutOrder) % 1, 0.8, 1)",
            "        end",
            "        if elapsed >= (duration or 10) then",
            "            connection:Disconnect()",
            "        end",
            "    end)",
            "end",
            "",
            "return startStorm",
        ]
        return "\n".join(lines)

    def _generic_template(self) -> str:
        lines = [
            "local function helper(...)",
            "    -- TODO: replace with a concrete implementation",
            "    return ...",
            "end",
            "",
            "return helper",
        ]
        return "\n".join(lines)

    def _format_name(self, name: str, *, kind: str) -> str:
        naming = self.heuristics.get("naming", {})
        case = naming.get(f"{kind}_case", "camel")
        if case == "pascal":
            return self._to_pascal(name)
        if case == "snake":
            return self._to_snake(name)
        return self._to_camel(name)

    def _to_pascal(self, value: str) -> str:
        parts = re.split(r"[_\-]", value)
        return "".join(part.capitalize() for part in parts)

    def _to_camel(self, value: str) -> str:
        pascal = self._to_pascal(value)
        return pascal[0].lower() + pascal[1:] if pascal else value

    def _to_snake(self, value: str) -> str:
        parts = re.split(r"[_\-]", value)
        return "_".join(part.lower() for part in parts if part)
