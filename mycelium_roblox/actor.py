"""Actor agent that generates Lua scripts based on planning guidance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .memory import MemoryStore
from .tools import LocalLLM


@dataclass
class ActionResult:
    step: str
    code: str
    notes: str


class Actor:
    """Actor agent responsible for producing Lua code."""

    def __init__(self, llm: LocalLLM, memory: MemoryStore) -> None:
        self.llm = llm
        self.memory = memory

    def _retrieve_relevant_skills(self, keywords: List[str]) -> Dict[str, str]:
        records = self.memory.fetch_skills()
        relevant: Dict[str, str] = {}
        for record in records:
            if any(keyword.lower() in record.code_summary.lower() for keyword in keywords):
                relevant[record.task] = record.code_summary
        return relevant

    def execute_plan(self, steps: List[str], task_description: str) -> List[ActionResult]:
        results: List[ActionResult] = []
        skills = self._retrieve_relevant_skills(["radar", "noise", "grid"])

        for step in steps:
            if "radar" in task_description.lower():
                code = self._generate_radar_script()
                notes = "Generated deterministic radar LocalScript using Perlin noise."
            else:
                prompt = f"Draft Roblox Lua code for step: {step}\n{task_description}"
                code = self.llm.complete(prompt)
                notes = "Used LLM stub to draft placeholder code."
            results.append(ActionResult(step=step, code=code, notes=notes))
        return results

    def _generate_radar_script(self) -> str:
        """Produce a self-contained LocalScript implementing the radar demo."""

        return """--!strict
-- LocalScript: Storm radar visualisation demo
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")

local playerGui = Players.LocalPlayer:WaitForChild("PlayerGui")
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "StormRadarDemo"
screenGui.ResetOnSpawn = false
screenGui.Parent = playerGui

local frame = Instance.new("Frame")
frame.Name = "RadarFrame"
frame.Size = UDim2.fromScale(0.6, 0.6)
frame.Position = UDim2.fromScale(0.2, 0.2)
frame.BorderSizePixel = 0
frame.BackgroundColor3 = Color3.fromRGB(5, 7, 12)
frame.Parent = screenGui

local gridWidth = 140
local gridHeight = 90
local pixels: {Frame} = {}

local function createPixel(x: number, y: number)
    local pixel = Instance.new("Frame")
    pixel.Size = UDim2.fromOffset(frame.AbsoluteSize.X / gridWidth, frame.AbsoluteSize.Y / gridHeight)
    pixel.BorderSizePixel = 0
    pixel.BackgroundColor3 = Color3.new(0, 0, 0)
    pixel.Name = string.format("Pixel_%d_%d", x, y)
    pixel.Parent = frame
    pixels[#pixels + 1] = pixel
    return pixel
end

local function initialiseGrid()
    frame:ClearAllChildren()
    table.clear(pixels)
    for y = 1, gridHeight do
        for x = 1, gridWidth do
            createPixel(x, y)
        end
    end
end

local function perlinNoise(x: number, y: number, t: number)
    return math.noise(x / 12, y / 12, t)
end

local swirlOffset = 0
local swirlSpeed = 0.35
local hesitationTimer = 0
local hesitationDelay = 2.5

local palette = {
    Color3.fromRGB(5, 7, 12),
    Color3.fromRGB(16, 52, 166),
    Color3.fromRGB(52, 132, 235),
    Color3.fromRGB(163, 230, 255),
    Color3.fromRGB(252, 252, 252)
}

local function lerpColor(a: Color3, b: Color3, t: number): Color3
    return Color3.new(
        a.R + (b.R - a.R) * t,
        a.G + (b.G - a.G) * t,
        a.B + (b.B - a.B) * t
    )
end

local function getColorFromPalette(sample: number): Color3
    if sample <= 0 then
        return palette[1]
    elseif sample >= 1 then
        return palette[#palette]
    end

    local scaled = sample * (#palette - 1)
    local idx = math.floor(scaled) + 1
    local alpha = scaled - math.floor(scaled)
    return lerpColor(palette[idx], palette[idx + 1], alpha)
end

local function updatePixelColors(dt: number)
    swirlOffset += dt * swirlSpeed
    hesitationTimer += dt

    if hesitationTimer >= hesitationDelay then
        swirlSpeed = math.clamp(swirlSpeed + (math.random() - 0.5) * 0.1, 0.15, 0.5)
        hesitationDelay = math.random(2, 5)
        hesitationTimer = 0
        print("Radar hesitation triggered", swirlSpeed, hesitationDelay)
    end

    local timeComponent = tick() * 0.25
    for index, pixel in ipairs(pixels) do
        local row = math.floor((index - 1) / gridWidth)
        local column = (index - 1) % gridWidth
        local swirl = math.sin((column + row) * 0.05 + swirlOffset)
        local noiseValue = perlinNoise(column * 0.12 + swirl, row * 0.12, timeComponent)
        local intensity = math.clamp((noiseValue + 1) / 2, 0, 1)
        pixel.BackgroundColor3 = getColorFromPalette(intensity)
    end
end

local function ensureLighting()
    Lighting.Brightness = 2
    Lighting.ClockTime = 21
    Lighting.FogEnd = 200
end

initialiseGrid()
ensureLighting()

RunService.Heartbeat:Connect(function(dt)
    updatePixelColors(dt)
end)
"""
