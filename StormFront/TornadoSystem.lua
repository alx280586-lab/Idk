local RunService = game:GetService("RunService")
local Debris = game:GetService("Debris")

local TornadoSystem = {}
TornadoSystem.__index = TornadoSystem

local DEFAULT_CONFIG = {
    BasePosition = Vector3.new(),
    EFScale = 1,
    SurfaceWind = Vector3.new(10, 0, 0),
    GroundRoughness = 0.6,
    LifeSpan = 240,
    SegmentCount = 6,
}

local EF_PROPERTIES = {
    [0] = {Radius = 35, Height = 220, PressureDrop = 12, Tangential = 55},
    [1] = {Radius = 50, Height = 280, PressureDrop = 18, Tangential = 70},
    [2] = {Radius = 70, Height = 360, PressureDrop = 26, Tangential = 92},
    [3] = {Radius = 95, Height = 460, PressureDrop = 38, Tangential = 115},
    [4] = {Radius = 130, Height = 620, PressureDrop = 52, Tangential = 140},
    [5] = {Radius = 165, Height = 720, PressureDrop = 72, Tangential = 170},
}

local function clampEF(value)
    return math.clamp(math.floor(value + 0.5), 0, 5)
end

local function spring(target, current, velocity, dt, stiffness, damping)
    stiffness = stiffness or 8
    damping = damping or 1.5
    local force = (target - current) * stiffness
    local accel = force - velocity * damping
    velocity = velocity + accel * dt
    current = current + velocity * dt
    return current, velocity
end

local function createCylinder(parent, radius, height, transparency, color)
    local part = Instance.new("Part")
    part.Name = "FunnelSegment"
    part.Shape = Enum.PartType.Cylinder
    part.Material = Enum.Material.Neon
    part.Anchored = true
    part.CanCollide = false
    part.Color = color or Color3.fromRGB(110, 110, 120)
    part.Transparency = transparency or 0.4
    part.Size = Vector3.new(radius * 2, height, radius * 2)
    part.Parent = parent
    return part
end

function TornadoSystem.new(config)
    config = config or {}
    local merged = table.clone(DEFAULT_CONFIG)
    for key, value in pairs(config) do
        merged[key] = value
    end

    local self = setmetatable({}, TornadoSystem)

    self.BasePosition = merged.BasePosition
    self._efScale = clampEF(merged.EFScale)
    self._surfaceWind = merged.SurfaceWind
    self._groundRoughness = merged.GroundRoughness
    self._lifeClock = 0
    self._lifeSpan = merged.LifeSpan
    self._ropeOut = false

    self._targetRadius = 0
    self._targetHeight = 0
    self._currentRadius = 0
    self._currentHeight = 0
    self._radiusVelocity = 0
    self._heightVelocity = 0
    self._pressureDrop = 0
    self._tangential = 0

    self.Model = Instance.new("Model")
    self.Model.Name = "AdvancedTornado"
    self.Model.Parent = workspace

    self._funnelFolder = Instance.new("Folder")
    self._funnelFolder.Name = "Funnel"
    self._funnelFolder.Parent = self.Model

    self._debrisFolder = Instance.new("Folder")
    self._debrisFolder.Name = "Debris"
    self._debrisFolder.Parent = self.Model

    self._segmentCount = merged.SegmentCount
    self._segments = {}

    for index = 1, self._segmentCount do
        local fraction = index / self._segmentCount
        local segment = createCylinder(self._funnelFolder, 20 + fraction * 40, 40 + fraction * 40, 0.55 - fraction * 0.05)
        self._segments[index] = segment
    end

    self:_configureFromEF(self._efScale)

    self._connection = RunService.Heartbeat:Connect(function(dt)
        self:_step(dt)
    end)

    return self
end

function TornadoSystem:_configureFromEF(efScale)
    local properties = EF_PROPERTIES[efScale] or EF_PROPERTIES[clampEF(efScale)]
    self._targetRadius = properties.Radius
    self._targetHeight = properties.Height
    self._pressureDrop = properties.PressureDrop
    self._tangential = properties.Tangential
end

function TornadoSystem:SetBasePosition(position)
    self.BasePosition = position
end

function TornadoSystem:SetSurfaceWind(windVector)
    self._surfaceWind = windVector
end

function TornadoSystem:SetIntensity(efScale)
    local newScale = clampEF(efScale)
    if newScale == self._efScale then
        return
    end
    self._efScale = newScale
    self:_configureFromEF(newScale)
end

function TornadoSystem:GetEFScale()
    return self._efScale
end

function TornadoSystem:GetSurfaceWind()
    return self._surfaceWind
end

function TornadoSystem:GetDamageEstimate()
    local groundWind = self._tangential + self._surfaceWind.Magnitude
    local normalized = math.clamp((groundWind - 60) / 120, 0, 1)
    return normalized
end

function TornadoSystem:RopeOut()
    self._ropeOut = true
    self._targetHeight = math.max(self._targetHeight * 0.35, 80)
    self._targetRadius = math.max(self._targetRadius * 0.4, 20)
end

local function spawnDebris(parent, position, tangential, surfaceWind)
    local shard = Instance.new("Part")
    shard.Name = "Debris"
    shard.Size = Vector3.new(math.random(1, 4), math.random(1, 3), math.random(2, 6))
    shard.Anchored = false
    shard.CanCollide = false
    shard.Color = Color3.fromRGB(120, 110, 100)
    shard.Material = Enum.Material.Wood
    shard.CFrame = CFrame.new(position + Vector3.new(0, 5, 0))
    shard.Parent = parent

    local radial = Vector3.new(math.random(-100, 100), 0, math.random(-100, 100))
    if radial.Magnitude < 1 then
        radial = Vector3.new(1, 0, 0)
    end
    radial = radial.Unit
    local lift = math.random(60, 120)
    shard.Velocity = radial * tangential + surfaceWind + Vector3.new(0, lift, 0)
    shard.RotVelocity = Vector3.new(math.random(-8, 8), math.random(-12, 12), math.random(-8, 8))

    Debris:AddItem(shard, 10)
end

function TornadoSystem:_updateSegments(dt)
    local wobble = math.sin(tick() * 2)
    local swirlSpeed = self._tangential / 10

    for index, segment in ipairs(self._segments) do
        local fraction = index / self._segmentCount
        local radius = self._currentRadius * math.clamp(fraction ^ 1.2, 0.35, 1)
        local height = self._currentHeight / self._segmentCount
        local yOffset = (index - 0.5) * height

        segment.Size = Vector3.new(math.max(radius * 2, 6), height, math.max(radius * 2, 6))

        local angle = tick() * swirlSpeed + fraction * math.pi * 0.5
        local wobbleOffset = Vector3.new(math.cos(angle) * wobble * 15, 0, math.sin(angle * 0.8) * wobble * 12)

        segment.CFrame = CFrame.new(self.BasePosition + wobbleOffset + Vector3.new(0, yOffset, 0)) * CFrame.Angles(math.rad(90), 0, 0)
        segment.Transparency = math.clamp(0.2 + (1 - fraction) * 0.5, 0.15, 0.9)
    end
end

function TornadoSystem:_emitDebris(dt)
    if math.random() > 0.4 then
        return
    end

    local spawnCount = math.random(1, 3)
    for _ = 1, spawnCount do
        spawnDebris(self._debrisFolder, self.BasePosition, self._tangential, self._surfaceWind)
    end
end

function TornadoSystem:_step(dt)
    if self._destroyed then
        return
    end

    self._lifeClock = self._lifeClock + dt

    self._currentRadius, self._radiusVelocity = spring(self._targetRadius, self._currentRadius, self._radiusVelocity, dt, 6, 1.4)
    self._currentHeight, self._heightVelocity = spring(self._targetHeight, self._currentHeight, self._heightVelocity, dt, 6, 1.4)

    self:_updateSegments(dt)
    self:_emitDebris(dt)

    if self._ropeOut then
        self._targetHeight = math.max(self._targetHeight - dt * 40, 60)
        self._targetRadius = math.max(self._targetRadius - dt * 15, 12)
        self._tangential = math.max(self._tangential - dt * 18, 40)
        if self._targetHeight <= 70 then
            self:Destroy()
            return
        end
    end

    if self._lifeClock > self._lifeSpan then
        self:RopeOut()
    end
end

function TornadoSystem:Destroy()
    if self._destroyed then
        return
    end
    self._destroyed = true

    if self._connection then
        self._connection:Disconnect()
        self._connection = nil
    end

    for _, segment in ipairs(self._segments) do
        if segment and segment.Parent then
            segment:Destroy()
        end
    end
    self._segments = {}

    if self._debrisFolder then
        self._debrisFolder:Destroy()
        self._debrisFolder = nil
    end

    if self._funnelFolder then
        self._funnelFolder:Destroy()
        self._funnelFolder = nil
    end

    if self.Model then
        self.Model:Destroy()
        self.Model = nil
    end
end

return TornadoSystem
