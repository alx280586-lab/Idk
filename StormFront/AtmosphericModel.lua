local RunService = game:GetService("RunService")

local AtmosphericModel = {}
AtmosphericModel.__index = AtmosphericModel

local DEFAULT_CONFIG = {
    Seed = tick(),
    BaseTemperature = 24,
    BaseDewPoint = 18,
    BasePressure = 998,
    DomainSize = Vector2.new(16000, 16000),
    GridResolution = 12,
    DayLengthSeconds = 1200,
    UpdateInterval = 2.5,
    FrontStrength = 0.5,
    TerrainInfluence = 0.4,
    LowLevelJetStrength = 18,
    UpperLevelJetStrength = 32,
    DrylineContrast = 8,
}

local function lerp(a, b, t)
    return a + (b - a) * t
end

local function clamp01(value)
    return math.clamp(value, 0, 1)
end

local function blendVector(a, b, t)
    return Vector3.new(
        lerp(a.X, b.X, t),
        lerp(a.Y, b.Y, t),
        lerp(a.Z, b.Z, t)
    )
end

function AtmosphericModel.new(config)
    config = config or {}
    local merged = table.clone(DEFAULT_CONFIG)
    for key, value in pairs(config) do
        merged[key] = value
    end

    local self = setmetatable({}, AtmosphericModel)

    self._config = merged
    self._seed = merged.Seed
    self._timeAccumulator = 0
    self._gridAccumulator = 0

    self._grid = {}
    self._outflowBoundaries = {}
    self._snapshot = {}

    self.Updated = Instance.new("BindableEvent")

    self:_rebuildGrid()

    self._connection = RunService.Heartbeat:Connect(function(dt)
        self:_step(dt)
    end)

    return self
end

function AtmosphericModel:_sampleNoise(x, z, time, scale, offset)
    scale = scale or 1
    offset = offset or 0
    local value = math.noise(
        (x + offset) / scale,
        (z - offset) / scale,
        time / scale
    )
    return value
end

function AtmosphericModel:_computeCell(xIndex, zIndex, diurnal, time)
    local cfg = self._config
    local resolution = cfg.GridResolution
    local domain = cfg.DomainSize

    local x = (xIndex - 0.5) / resolution
    local z = (zIndex - 0.5) / resolution

    local domainX = lerp(-domain.X * 0.5, domain.X * 0.5, x)
    local domainZ = lerp(-domain.Y * 0.5, domain.Y * 0.5, z)

    local terrainNoise = self:_sampleNoise(domainX, domainZ, time, 3200, self._seed) * cfg.TerrainInfluence
    local moistureNoise = self:_sampleNoise(domainX, domainZ, time * 0.5, 2100, self._seed * 0.3)
    local shearNoise = self:_sampleNoise(domainX, domainZ, time * 0.8, 4200, self._seed * 1.3)

    local dryline = math.clamp(math.sin((domainX + time * 150) / 2800), -1, 1)
    local moistureGradient = clamp01(0.5 + moistureNoise * 0.5 + dryline * 0.35)

    local temperature = cfg.BaseTemperature + diurnal * 6 + terrainNoise * 5 - (1 - moistureGradient) * cfg.DrylineContrast
    local dewPoint = cfg.BaseDewPoint + moistureGradient * 8 + terrainNoise * 1.5
    local pressure = cfg.BasePressure - diurnal * 9 - terrainNoise * 5 - moistureNoise * 2

    local lapseRate = 5.2 + clamp01((temperature - dewPoint) / 12) * 5
    local cape = math.clamp((temperature - dewPoint * 0.8) * moistureGradient * 220, 0, 6000)
    local cin = math.clamp((1 - moistureGradient) * 120 + math.max(0, 20 - diurnal * 30), 0, 350)

    local helicityBase = clamp01(moistureGradient * 0.8 + shearNoise * 0.6)
    local shearVector = blendVector(
        Vector3.new(1, 0, 0) * cfg.LowLevelJetStrength,
        Vector3.new(-0.3, 0, 1).Unit * cfg.UpperLevelJetStrength,
        helicityBase
    )
    local surfaceWind = blendVector(
        Vector3.new(1, 0, 0) * cfg.LowLevelJetStrength * (0.4 + moistureGradient * 0.3),
        shearVector,
        0.25 + moistureGradient * 0.35
    )

    local helicity = math.clamp(surfaceWind.Magnitude * shearVector.Magnitude * helicityBase * 0.6, 80, 850)
    local stormMotion = surfaceWind:Lerp(shearVector, 0.35)

    local thetaE = temperature + moistureGradient * 12
    local thetaGradient = math.abs(self:_sampleNoise(domainX + 600, domainZ, time, 1800, self._seed * 2) - self:_sampleNoise(domainX - 600, domainZ, time, 1800, self._seed * 2))
    local outflow = clamp01(thetaGradient * (cape / 4500))

    return {
        Position = Vector3.new(domainX, 0, domainZ),
        Temperature = temperature,
        DewPoint = dewPoint,
        Pressure = pressure,
        CAPE = cape,
        CIN = cin,
        Helicity = helicity,
        LapseRate = lapseRate,
        Moisture = moistureGradient,
        SurfaceWind = surfaceWind,
        ShearVector = shearVector,
        StormMotion = stormMotion,
        ThetaE = thetaE,
        Outflow = outflow,
    }
end

function AtmosphericModel:_rebuildGrid()
    local cfg = self._config
    local resolution = cfg.GridResolution
    local dayLength = cfg.DayLengthSeconds
    local absoluteTime = tick() + self._seed * 0.1
    local diurnal = math.sin((self._timeAccumulator / dayLength) * math.pi * 2)

    local totalTemp, totalDew, totalPress = 0, 0, 0
    local totalCape, totalCin, totalHelicity = 0, 0, 0
    local totalWind = Vector3.new()
    local totalStormMotion = Vector3.new()

    local outflowBoundaries = {}

    for x = 1, resolution do
        self._grid[x] = self._grid[x] or {}
        for z = 1, resolution do
            local cell = self:_computeCell(x, z, diurnal, absoluteTime)
            self._grid[x][z] = cell

            totalTemp = totalTemp + cell.Temperature
            totalDew = totalDew + cell.DewPoint
            totalPress = totalPress + cell.Pressure
            totalCape = totalCape + cell.CAPE
            totalCin = totalCin + cell.CIN
            totalHelicity = totalHelicity + cell.Helicity
            totalWind = totalWind + cell.SurfaceWind
            totalStormMotion = totalStormMotion + cell.StormMotion
        end
    end

    local cellCount = resolution * resolution
    self._snapshot = {
        Temperature = totalTemp / cellCount,
        DewPoint = totalDew / cellCount,
        Pressure = totalPress / cellCount,
        CAPE = totalCape / cellCount,
        CIN = totalCin / cellCount,
        Helicity = totalHelicity / cellCount,
        LapseRate = 5 + (totalCape / cellCount) / 900,
        SurfaceWind = totalWind / cellCount,
        StormMotion = totalStormMotion / cellCount,
    }

    for x = 2, resolution - 1 do
        for z = 2, resolution - 1 do
            local cell = self._grid[x][z]
            local east = self._grid[x + 1][z]
            local west = self._grid[x - 1][z]
            local north = self._grid[x][z + 1]
            local south = self._grid[x][z - 1]

            local gradient = math.abs(east.ThetaE - west.ThetaE) + math.abs(north.ThetaE - south.ThetaE)
            local outflowStrength = math.clamp(cell.Outflow * gradient * 0.5, 0, 1)
            if outflowStrength > 0.25 then
                table.insert(outflowBoundaries, {
                    Position = cell.Position,
                    Strength = outflowStrength,
                    Normal = (east.Position - west.Position).Unit,
                })
            end
        end
    end

    table.sort(outflowBoundaries, function(a, b)
        return a.Strength > b.Strength
    end)

    self._outflowBoundaries = outflowBoundaries
    self.Updated:Fire(self._snapshot)
end

function AtmosphericModel:_step(dt)
    self._timeAccumulator = self._timeAccumulator + dt
    self._gridAccumulator = self._gridAccumulator + dt

    if self._gridAccumulator >= self._config.UpdateInterval then
        self._gridAccumulator = 0
        self:_rebuildGrid()
    end
end

function AtmosphericModel:GetSnapshot()
    return table.clone(self._snapshot)
end

local function clampToGridIndex(value, resolution)
    return math.clamp(math.floor(value), 1, resolution)
end

function AtmosphericModel:SampleAt(position)
    local cfg = self._config
    local resolution = cfg.GridResolution
    local domain = cfg.DomainSize

    local xNorm = (position.X + domain.X * 0.5) / domain.X
    local zNorm = (position.Z + domain.Y * 0.5) / domain.Y

    local x = clampToGridIndex(xNorm * resolution + 1, resolution)
    local z = clampToGridIndex(zNorm * resolution + 1, resolution)

    local cell = self._grid[x] and self._grid[x][z]
    if not cell then
        return self:GetSnapshot()
    end

    return table.clone(cell)
end

function AtmosphericModel:GetOutflowBoundaries(maxCount)
    maxCount = maxCount or 8
    local boundaries = {}
    for index = 1, math.min(maxCount, #self._outflowBoundaries) do
        boundaries[index] = self._outflowBoundaries[index]
    end
    return boundaries
end

function AtmosphericModel:ComputeTornadoPotential(position)
    local env = position and self:SampleAt(position) or self:GetSnapshot()

    local capeScore = clamp01(env.CAPE / 3500)
    local helicityScore = clamp01(env.Helicity / 450)
    local shearScore = clamp01(env.ShearVector and env.ShearVector.Magnitude / 45 or 0)
    local moistureScore = clamp01((env.DewPoint - 10) / 10)
    local cinPenalty = clamp01(env.CIN / 200)

    local potential = clamp01((capeScore * 0.35 + helicityScore * 0.3 + shearScore * 0.2 + moistureScore * 0.25) - cinPenalty * 0.35)
    return potential
end

function AtmosphericModel:GetDomainSize()
    return self._config.DomainSize
end

function AtmosphericModel:Destroy()
    if self._connection then
        self._connection:Disconnect()
        self._connection = nil
    end

    if self.Updated then
        self.Updated:Destroy()
        self.Updated = nil
    end

    self._grid = nil
    self._outflowBoundaries = nil
end

return AtmosphericModel
