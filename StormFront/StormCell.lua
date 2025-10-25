local RunService = game:GetService("RunService")
local Debris = game:GetService("Debris")

local TornadoSystem = require(script.Parent.TornadoSystem)

local StormCell = {}
StormCell.__index = StormCell

local function lerp(a, b, t)
    return a + (b - a) * t
end

local STAGES = {
    CUMULUS = "Cumulus",
    TOWERING = "Towering",
    MATURE = "Mature",
    SUPERCELL = "Supercell",
    TORNADOGENESIS = "Tornadogenesis",
    TORNADO = "Tornado",
    ROPE_OUT = "RopeOut",
    DISSIPATING = "Dissipating",
}

local ORDERED_STAGES = {
    STAGES.CUMULUS,
    STAGES.TOWERING,
    STAGES.MATURE,
    STAGES.SUPERCELL,
    STAGES.TORNADOGENESIS,
    STAGES.TORNADO,
    STAGES.ROPE_OUT,
    STAGES.DISSIPATING,
}

local DEFAULT_CONFIG = {
    Seed = tick(),
    BasePosition = Vector3.new(),
    InitialStage = STAGES.CUMULUS,
    TargetType = "DiscreteSupercell",
    Motion = Vector3.new(12, 0, 4),
}

local function createCloudLayer(parent, radius, height, transparency, color)
    local part = Instance.new("Part")
    part.Name = "CloudLayer"
    part.Anchored = true
    part.CanCollide = false
    part.Material = Enum.Material.Neon
    part.Color = color or Color3.fromRGB(190, 190, 200)
    part.Transparency = transparency or 0.35
    part.Size = Vector3.new(radius * 2, height, radius * 2)
    part.CFrame = CFrame.new(parent.BasePosition + Vector3.new(0, height * 0.5, 0))
    part.Parent = parent.Model
    return part
end

local function createPrecipCore(parent)
    local part = Instance.new("Part")
    part.Name = "PrecipCore"
    part.Anchored = true
    part.CanCollide = false
    part.Transparency = 0.6
    part.Color = Color3.fromRGB(80, 90, 110)
    part.Material = Enum.Material.Glass
    part.Size = Vector3.new(120, 300, 120)
    part.CFrame = CFrame.new(parent.BasePosition + Vector3.new(0, 150, 0))
    part.Parent = parent.Model
    return part
end

local function createLightningEmitter(parent)
    local folder = Instance.new("Folder")
    folder.Name = "Lightning"
    folder.Parent = parent.Model
    return folder
end

local function stageOrder(stage)
    for index, value in ipairs(ORDERED_STAGES) do
        if value == stage then
            return index
        end
    end
    return 1
end

function StormCell.new(config)
    config = config or {}
    local merged = table.clone(DEFAULT_CONFIG)
    for key, value in pairs(config) do
        merged[key] = value
    end

    local self = setmetatable({}, StormCell)

    self.BasePosition = merged.BasePosition
    self.Position = merged.BasePosition
    self.Stage = merged.InitialStage
    self.TargetType = merged.TargetType
    self.Velocity = merged.Motion

    self.Age = 0
    self.PeakIntensity = 0
    self.UpdraftStrength = 0
    self.RotationStrength = 0
    self.MesocycloneDepth = 0
    self.RadarSignature = ""
    self.PrecipitationRate = 0
    self.HailSize = 0
    self.LightningTimer = 0
    self.TornadoPotential = 0
    self.Tornado = nil
    self._dissipationClock = 0

    self.Model = Instance.new("Model")
    self.Model.Name = "StormCell"
    self.Model.Parent = workspace

    self._cloudBase = createCloudLayer(self, 350, 60, 0.55, Color3.fromRGB(130, 130, 140))
    self._anvil = createCloudLayer(self, 650, 45, 0.65, Color3.fromRGB(210, 210, 220))
    self._precipCore = createPrecipCore(self)
    self._lightning = createLightningEmitter(self)

    self._visualConnection = RunService.Heartbeat:Connect(function(dt)
        self:_updateVisuals(dt)
    end)

    return self
end

function StormCell:_updateVisuals(dt)
    if not self.Model.Parent then
        return
    end

    local wobble = Vector3.new(math.sin(tick() * 0.2 + self.Age) * 35, 0, math.cos(tick() * 0.16 + self.Age * 0.6) * 35)
    local basePosition = self.Position + wobble

    local updraftFraction = math.clamp(self.UpdraftStrength / 60, 0, 1)
    local rotationFraction = math.clamp(self.RotationStrength / 50, 0, 1)

    if self._cloudBase then
        self._cloudBase.Size = Vector3.new(lerp(260, 480, updraftFraction), 60, lerp(260, 480, rotationFraction))
        self._cloudBase.CFrame = CFrame.new(basePosition + Vector3.new(0, 320, 0)) * CFrame.Angles(0, math.rad(self.Age % 360), 0)
        self._cloudBase.Transparency = lerp(0.25, 0.7, 1 - updraftFraction)
    end

    if self._anvil then
        self._anvil.Size = Vector3.new(lerp(600, 1200, updraftFraction), 45, lerp(600, 1200, updraftFraction))
        self._anvil.CFrame = CFrame.new(basePosition + Vector3.new(0, 700, 0))
        self._anvil.Transparency = lerp(0.4, 0.8, math.clamp(self.Age / 120, 0, 1))
    end

    if self._precipCore then
        local precipFraction = math.clamp(self.PrecipitationRate / 120, 0, 1)
        self._precipCore.Size = Vector3.new(lerp(80, 260, precipFraction), lerp(160, 420, precipFraction), lerp(80, 260, precipFraction))
        self._precipCore.CFrame = CFrame.new(basePosition + Vector3.new(0, self._precipCore.Size.Y * 0.5, -180 + rotationFraction * 120))
        self._precipCore.Transparency = lerp(0.45, 0.82, 1 - precipFraction)
    end

    self.LightningTimer = self.LightningTimer - dt
    if self.LightningTimer <= 0 then
        self.LightningTimer = math.random(6, 18) / math.max(0.8, self.UpdraftStrength / 30)
        if self._lightning then
            local bolt = Instance.new("Part")
            bolt.Name = "LightningBolt"
            bolt.Anchored = true
            bolt.CanCollide = false
            bolt.Material = Enum.Material.Neon
            bolt.Color = Color3.fromRGB(255, 250, 200)
            bolt.Transparency = 0.3
            bolt.Size = Vector3.new(3, math.random(220, 420), 3)
            bolt.CFrame = CFrame.new(basePosition + Vector3.new(math.random(-180, 180), math.random(260, 600), math.random(-180, 180)))
            bolt.Parent = self._lightning
            Debris:AddItem(bolt, 0.25)
        end
    end

    if self.Tornado then
        self.Tornado:SetBasePosition(self.Position + Vector3.new(rotationFraction * 45, 0, -120))
    end
end

local stageThresholds = {
    [STAGES.CUMULUS] = 20,
    [STAGES.TOWERING] = 40,
    [STAGES.MATURE] = 60,
    [STAGES.SUPERCELL] = 75,
    [STAGES.TORNADOGENESIS] = 85,
    [STAGES.TORNADO] = 85,
    [STAGES.ROPE_OUT] = 45,
    [STAGES.DISSIPATING] = 15,
}

local function computeIntensity(env, updraft, rotation)
    local capeTerm = env.CAPE / 4500
    local helicityTerm = env.Helicity / 600
    local moistureTerm = env.Moisture or math.clamp((env.DewPoint - 10) / 10, 0, 1)
    local shearTerm = (env.ShearVector and env.ShearVector.Magnitude or 0) / 40

    local updraftTerm = updraft / 65
    local rotationTerm = rotation / 60

    return math.clamp((capeTerm * 0.35) + (helicityTerm * 0.25) + (moistureTerm * 0.15) + (shearTerm * 0.15) + (updraftTerm * 0.3) + (rotationTerm * 0.35), 0, 1.2)
end

function StormCell:_advanceStage(intensity)
    local threshold = stageThresholds[self.Stage] or 25
    if intensity * 100 > threshold + 10 then
        local nextStageIndex = stageOrder(self.Stage) + 1
        self.Stage = ORDERED_STAGES[math.clamp(nextStageIndex, 1, #ORDERED_STAGES)]
    elseif intensity * 100 < threshold - 20 then
        local nextStageIndex = stageOrder(self.Stage) - 1
        self.Stage = ORDERED_STAGES[math.clamp(nextStageIndex, 1, #ORDERED_STAGES)]
    end
end

function StormCell:_updateTornado(env)
    local tornadoPotential = env.TornadoPotential or computeIntensity(env, self.UpdraftStrength, self.RotationStrength)
    local tornadicThreshold = math.clamp(tornadoPotential * 1.2, 0, 1)

    self.TornadoPotential = tornadoPotential

    if (self.Stage == STAGES.TORNADOGENESIS or self.Stage == STAGES.TORNADO) and tornadoPotential > 0.55 then
        local efScale = math.clamp(math.floor(tornadoPotential * 6), 0, 5)
        if not self.Tornado then
            self.Tornado = TornadoSystem.new({
                BasePosition = self.Position,
                EFScale = efScale,
                SurfaceWind = env.SurfaceWind,
                GroundRoughness = 0.4 + env.Moisture * 0.6,
            })
        else
            self.Tornado:SetIntensity(efScale)
            self.Tornado:SetSurfaceWind(env.SurfaceWind)
        end
    elseif self.Tornado and (self.Stage == STAGES.ROPE_OUT or tornadoPotential < 0.4) then
        self.Tornado:RopeOut()
        self.Tornado = nil
    end

    return tornadicThreshold
end

function StormCell:Update(dt, atmosphere)
    self.Age = self.Age + dt
    self.Position = self.Position + self.Velocity * dt

    local env = atmosphere:SampleAt(self.Position)
    env.TornadoPotential = atmosphere:ComputeTornadoPotential(self.Position)

    self.Velocity = env.StormMotion or self.Velocity

    local lift = math.max(0, env.CAPE / 200 - env.CIN)
    local moistureFlux = env.Moisture * 80
    local shear = env.ShearVector and env.ShearVector.Magnitude or env.SurfaceWind.Magnitude

    self.UpdraftStrength = math.clamp(lift * 0.6 + moistureFlux * 0.1, 0, 90)
    self.RotationStrength = math.clamp((env.Helicity / 6) + shear * 0.8, 0, 90)
    self.MesocycloneDepth = math.clamp(env.LapseRate * 45, 120, 600)
    self.PrecipitationRate = math.clamp(env.Moisture * env.CAPE / 40, 0, 160)
    self.HailSize = math.clamp(env.CAPE / 800 + env.Helicity / 500, 0, 5)

    local intensity = computeIntensity(env, self.UpdraftStrength, self.RotationStrength)
    self.PeakIntensity = math.max(self.PeakIntensity, intensity)

    self:_advanceStage(intensity)
    local tornadoThreshold = self:_updateTornado(env)

    if self.Stage == STAGES.ROPE_OUT and self.Tornado then
        self.Tornado:SetIntensity(math.max(self.Tornado:GetEFScale() - dt * 0.5, 0))
    end

    self.RadarSignature = string.format("Hook: %.2f  Inflow: %.2f  Echo: %.2f", env.Helicity / 600, env.Moisture, self.PrecipitationRate / 160)

    if self.Stage == STAGES.DISSIPATING then
        self._dissipationClock = self._dissipationClock + dt
    else
        self._dissipationClock = 0
    end

    return {
        Stage = self.Stage,
        Position = self.Position,
        Velocity = self.Velocity,
        Intensity = intensity,
        PeakIntensity = self.PeakIntensity,
        UpdraftStrength = self.UpdraftStrength,
        RotationStrength = self.RotationStrength,
        MesocycloneDepth = self.MesocycloneDepth,
        PrecipitationRate = self.PrecipitationRate,
        HailSize = self.HailSize,
        TornadoPotential = tornadoThreshold,
        HasTornado = self.Tornado ~= nil,
        Tornado = self.Tornado,
        Environment = env,
    }
end

function StormCell:IsExpired()
    return (self.Stage == STAGES.DISSIPATING and (self._dissipationClock > 120 or self.Age > 900)) or self.Age > 1500
end

function StormCell:Destroy()
    if self._visualConnection then
        self._visualConnection:Disconnect()
        self._visualConnection = nil
    end

    if self.Tornado then
        self.Tornado:Destroy()
        self.Tornado = nil
    end

    if self.Model then
        self.Model:Destroy()
        self.Model = nil
    end
end

return StormCell
