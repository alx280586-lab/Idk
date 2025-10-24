"""Generate a large set of Luau example scripts for training."""
from __future__ import annotations

from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent / "data" / "examples"
BASE_PATH.mkdir(parents=True, exist_ok=True)

TAGS = [
    "NPC",
    "Guard",
    "Healer",
    "Vendor",
    "Storm",
    "Beacon",
    "Defense",
    "Speedway",
    "Explorer",
    "Miner",
]

TEMPLATES = {
    "spawn": """
local CollectionService = game:GetService("CollectionService")

local function {func_name}(tagName)
    local candidates = CollectionService:GetTagged(tagName or "{tag}")
    if #candidates == 0 then
        warn("No spawn points tagged", tagName)
        return nil
    end
    local index = math.random(1, #candidates)
    local chosen = candidates[index]
    return chosen.Position
end

return {func_name}
""".strip(),
    "teleport": """
local Players = game:GetService("Players")

local function {func_name}(playerName, destination)
    local player = Players:FindFirstChild(playerName)
    if not player or not player.Character then
        return false
    end
    local root = player.Character:FindFirstChild("HumanoidRootPart")
    if root then
        root.CFrame = destination.CFrame
        return true
    end
    return false
end

return {func_name}
""".strip(),
    "remote": """
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function {func_name}(eventName, ...)
    local remote = ReplicatedStorage:FindFirstChild(eventName)
    if remote and remote.IsA and remote:IsA("RemoteEvent") then
        remote:FireServer(...)
        return true
    end
    return false
end

return {func_name}
""".strip(),
    "path": """
local PathfindingService = game:GetService("PathfindingService")

local function {func_name}(startPos, endPos)
    local agentParameters = {{
        AgentRadius = 4,
        AgentHeight = 5,
        AgentCanJump = true,
    }}
    local path = PathfindingService:CreatePath(agentParameters)
    path:ComputeAsync(startPos, endPos)
    if path.Status ~= Enum.PathStatus.Success then
        return nil
    end
    return path:GetWaypoints()
end

return {func_name}
""".strip(),
    "ui": """
local TweenService = game:GetService("TweenService")

local function {func_name}(guiObject, visible)
    if not guiObject then
        return
    end
    local goal = {{ Transparency = visible and 0 or 1 }}
    local tweenInfo = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
    local tween = TweenService:Create(guiObject, tweenInfo, goal)
    tween:Play()
end

return {func_name}
""".strip(),
}


def to_pascal(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_"))


def build_function_name(intent: str, index: int) -> str:
    base = f"{intent}_helper_{index:03d}"
    return to_pascal(base)


def main() -> None:
    total = 0
    intents = list(TEMPLATES.keys())
    for idx in range(1, 201):
        intent = intents[(idx - 1) % len(intents)]
        func_name = build_function_name(intent, idx)
        tag = TAGS[(idx - 1) % len(TAGS)]
        template = TEMPLATES[intent]
        code = template.format(func_name=func_name, tag=tag)
        path = BASE_PATH / f"generated_{idx:03d}_{intent}.lua"
        path.write_text(code + "\n", encoding="utf-8")
        total += 1
    print(f"Wrote {total} example scripts to {BASE_PATH}")


if __name__ == "__main__":
    main()
