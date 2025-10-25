local RunService = game:GetService("RunService")

local AtmosphericModel = require(script.Parent.AtmosphericModel)
local StormCell = require(script.Parent.StormCell)

local StormManager = {}
StormManager.__index = StormManager

local DEFAULT_CONFIG = {
    MaxStorms = 5,
    StormSpawnInterval = 75,
    Atmosphere = {},
    BoundarySpawnBias = 0.65,
    BackgroundSpawnBias = 0.25,
    MinimumPotential = 0.45,
}

function StormManager.new(config)
    config = config or {}
    local merged = table.clone(DEFAULT_CONFIG)
    for key, value in pairs(config) do
        merged[key] = value
    end

    local self = setmetatable({}, StormManager)

    self._config = merged
    self._atmosphere = AtmosphericModel.new(merged.Atmosphere)
    self._storms = {}
    self._spawnClock = 0

    self.StormSpawned = Instance.new("BindableEvent")
    self.StormUpdated = Instance.new("BindableEvent")
    self.StormDissipated = Instance.new("BindableEvent")

    self._connection = RunService.Heartbeat:Connect(function(dt)
        self:_step(dt)
    end)

    return self
end

local function makeStormConfig(boundary, env, seed)
    local typeRoll = env.Helicity > 400 and "DiscreteSupercell" or "MultiCell"
    if boundary and boundary.Strength > 0.65 then
        typeRoll = "ClassicSupercell"
    elseif env.CAPE > 3500 and env.ShearVector and env.ShearVector.Magnitude > 30 then
        typeRoll = "HP Supercell"
    elseif env.CAPE < 1200 then
        typeRoll = "Pulse"
    end

    local motion = env.StormMotion or env.SurfaceWind or Vector3.new(12, 0, 0)
    return {
        Seed = seed,
        BasePosition = boundary and boundary.Position or env.Position or Vector3.new(),
        TargetType = typeRoll,
        Motion = Vector3.new(motion.X, 0, motion.Z),
    }
end

function StormManager:_spawnStorm(boundary)
    if #self._storms >= self._config.MaxStorms then
        return
    end

    local env
    local spawnPosition

    if boundary then
        env = self._atmosphere:SampleAt(boundary.Position)
        spawnPosition = boundary.Position + Vector3.new(math.random(-450, 450), 0, math.random(-450, 450))
    else
        local domain = self._atmosphere:GetDomainSize()
        spawnPosition = Vector3.new(
            math.random(-domain.X / 2, domain.X / 2),
            0,
            math.random(-domain.Y / 2, domain.Y / 2)
        )
        env = self._atmosphere:SampleAt(spawnPosition)
    end

    local potential = self._atmosphere:ComputeTornadoPotential(spawnPosition)
    if potential < self._config.MinimumPotential then
        return
    end

    env.Position = spawnPosition
    local stormConfig = makeStormConfig(boundary, env, tick() * 1000 % 1e7)
    stormConfig.BasePosition = spawnPosition

    local storm = StormCell.new(stormConfig)
    table.insert(self._storms, storm)
    self.StormSpawned:Fire(storm, env)
end

function StormManager:_updateStorms(dt)
    for index = #self._storms, 1, -1 do
        local storm = self._storms[index]
        local state = storm:Update(dt, self._atmosphere)

        self.StormUpdated:Fire(storm, state)

        if storm:IsExpired() then
            self.StormDissipated:Fire(storm, state)
            storm:Destroy()
            table.remove(self._storms, index)
        end
    end
end

function StormManager:_step(dt)
    self._spawnClock = self._spawnClock + dt

    if self._spawnClock >= self._config.StormSpawnInterval then
        self._spawnClock = 0

        local boundaries = self._atmosphere:GetOutflowBoundaries()
        local chosenBoundary
        if #boundaries > 0 and math.random() < self._config.BoundarySpawnBias then
            chosenBoundary = boundaries[math.random(1, math.min(#boundaries, 3))]
        elseif math.random() < self._config.BackgroundSpawnBias then
            chosenBoundary = nil
        end

        self:_spawnStorm(chosenBoundary)
    end

    self:_updateStorms(dt)
end

function StormManager:GetAtmosphere()
    return self._atmosphere
end

function StormManager:GetStorms()
    return self._storms
end

function StormManager:Destroy()
    if self._connection then
        self._connection:Disconnect()
        self._connection = nil
    end

    if self.StormSpawned then
        self.StormSpawned:Destroy()
        self.StormSpawned = nil
    end

    if self.StormUpdated then
        self.StormUpdated:Destroy()
        self.StormUpdated = nil
    end

    if self.StormDissipated then
        self.StormDissipated:Destroy()
        self.StormDissipated = nil
    end

    if self._atmosphere then
        self._atmosphere:Destroy()
        self._atmosphere = nil
    end

    for _, storm in ipairs(self._storms) do
        storm:Destroy()
    end
    self._storms = {}
end

return StormManager
