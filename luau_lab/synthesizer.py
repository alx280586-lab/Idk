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
        summary = self._summarize(code)
        if summary:
            explanation.append(summary)
        for idx, line in enumerate(code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("local CollectionService"):
                explanation.append(
                    f"Line {idx}: Grab CollectionService so we can pull objects by tag."
                )
            elif "GetTagged" in stripped:
                explanation.append(
                    f"Line {idx}: Build a list of parts carrying the requested tag."
                )
            elif "math.random" in stripped:
                explanation.append(
                    f"Line {idx}: Use math.random for a simple, uniform choice of spawn point."
                )
            elif "Random.new" in stripped:
                explanation.append(
                    f"Line {idx}: Spin up a Random instance so we control the RNG and avoid globals."
                )
            elif "warn(" in stripped:
                explanation.append(
                    f"Line {idx}: Warn you immediately if we can’t find anything to work with."
                )
            elif "Position" in stripped and "return" in stripped:
                explanation.append(
                    f"Line {idx}: Hand back the Vector3 position so callers can place characters there."
                )
            elif "HumanoidRootPart" in stripped and "CFrame" in stripped:
                explanation.append(
                    f"Line {idx}: Snap the player’s HumanoidRootPart to the destination so teleporting is instant."
                )
            elif "RemoteEvent" in stripped and "FireServer" in stripped:
                explanation.append(
                    f"Line {idx}: Fire the remote safely from the client towards the server."
                )
            elif "TweenService" in stripped and "Create" in stripped:
                explanation.append(
                    f"Line {idx}: Animate the GUI transition with a quick tween so it feels polished."
                )
            elif stripped.startswith("return"):
                explanation.append(
                    f"Line {idx}: Return the helper so other scripts can require this module."
                )
            else:
                explanation.append(f"Line {idx}: {stripped}")
        return explanation

    # Template helpers -------------------------------------------------

    def _spawn_template(self, request: SynthesisRequest) -> str:
        prefer_random_new = self.heuristics.get("preferences", {}).get("prefer_random_new", False)
        function_name = self._format_name("pickRandomSpawn", kind="function")
        tag_parameter = request.tag or "NPC"
        rng_block = (
            "    local rng = Random.new()\n"
            "    local index = rng:NextInteger(1, #candidates)\n"
            "    local chosen = candidates[index]"
        ) if prefer_random_new else (
            "    local index = math.random(1, #candidates)\n"
            "    local chosen = candidates[index]"
        )

        lines = [
            "local CollectionService = game:GetService(\"CollectionService\")",
            "",
            f"local function {function_name}(tagName)",
            "    local candidates = CollectionService:GetTagged(tagName or \"%s\")" % tag_parameter,
            "    if #candidates == 0 then",
            "        warn(\"No spawn points tagged\", tagName)",
            "        return nil",
            "    end",
            rng_block,
            "    return chosen.Position",
            "end",
            "",
            "return %s" % function_name,
        ]
        return "\n".join(lines)

    def _teleport_template(self) -> str:
        lines = [
            "local Players = game:GetService(\"Players\")",
            "",
            "local function teleportPlayer(playerName, destination)",
            "    local player = Players:FindFirstChild(playerName)",
            "    if not player or not player.Character then",
            "        return false",
            "    end",
            "    local root = player.Character:FindFirstChild(\"HumanoidRootPart\")",
            "    if root then",
            "        root.CFrame = destination.CFrame",
            "        return true",
            "    end",
            "    return false",
            "end",
            "",
            "return teleportPlayer",
        ]
        return "\n".join(lines)

    def _storm_template(self) -> str:
        lines = [
            "local RunService = game:GetService(\"RunService\")",
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

    def _summarize(self, code: str) -> Optional[str]:
        lowered = code.lower()
        function_name_match = re.search(r"function\s+([a-zA-Z0-9_]+)", code)
        fn_name = function_name_match.group(1) if function_name_match else "the helper"
        if "collectionservice" in lowered and "gettagged" in lowered:
            return (
                f"This helper '{fn_name}' looks up CollectionService tags and hands back a random spawn point."
            )
        if "humanoidrootpart" in lowered and "cframe" in lowered:
            return f"'{fn_name}' teleports a player straight to whatever part you pass in."
        if "remoteevent" in lowered and "fireserver" in lowered:
            return f"'{fn_name}' safely fires a RemoteEvent by name if it exists."
        if "tweenservice" in lowered and "create" in lowered:
            return f"'{fn_name}' animates a GUI element’s visibility with a quick tween."
        if "pathfindingservice" in lowered and "createpath" in lowered:
            return f"'{fn_name}' computes path waypoints using PathfindingService."
        return None
