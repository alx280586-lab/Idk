local Instrumentation = {}
Instrumentation.__index = Instrumentation

function Instrumentation.new(atmosphere)
    local self = setmetatable({}, Instrumentation)

    self._atmosphere = atmosphere
    self.Readouts = {
        Temperature = 0,
        DewPoint = 0,
        Pressure = 0,
        WindSpeed = 0,
        WindDirection = Vector3.new(),
        CAPE = 0,
        CIN = 0,
        Helicity = 0,
        StormMotion = Vector3.new(),
    }

    self._connection = atmosphere.Updated.Event:Connect(function(snapshot)
        self:_updateSnapshot(snapshot)
    end)

    return self
end

function Instrumentation:_updateSnapshot(snapshot)
    self.Readouts.Temperature = snapshot.Temperature
    self.Readouts.DewPoint = snapshot.DewPoint
    self.Readouts.Pressure = snapshot.Pressure
    local surfaceWind = snapshot.SurfaceWind
    if surfaceWind.Magnitude < 1e-3 then
        surfaceWind = Vector3.new()
    end
    self.Readouts.WindSpeed = surfaceWind.Magnitude
    self.Readouts.WindDirection = surfaceWind.Magnitude > 0 and surfaceWind.Unit or Vector3.new()
    self.Readouts.CAPE = snapshot.CAPE
    self.Readouts.CIN = snapshot.CIN
    self.Readouts.Helicity = snapshot.Helicity
    self.Readouts.StormMotion = snapshot.StormMotion
end

function Instrumentation:SampleAt(position)
    local env = self._atmosphere:SampleAt(position)
    env.TornadoPotential = self._atmosphere:ComputeTornadoPotential(position)
    return env
end

local function directionToText(vector)
    local horizontal = Vector2.new(vector.X, vector.Z)
    if horizontal.Magnitude < 1e-4 then
        return "Calm"
    end
    local heading = math.deg(math.atan2(horizontal.Y, horizontal.X))
    local headings = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
    local index = math.floor(((heading + 360) % 360) / 45 + 0.5) % 8 + 1
    return headings[index]
end

function Instrumentation:GetFormattedReadout(position)
    local env = position and self:SampleAt(position) or self.Readouts
    local surfaceWind = env.SurfaceWind or (env.WindDirection and env.WindDirection * (env.WindSpeed or self.Readouts.WindSpeed)) or Vector3.new()
    local stormMotion = env.StormMotion or self.Readouts.StormMotion
    local directionText = directionToText(surfaceWind)
    local stormMotionText = directionToText(stormMotion)

    return string.format(
        "Temp: %.1f°C (Dew %.1f°C)\nPressure: %.1f hPa\nWind: %.1f m/s %s\nStorm Motion: %.1f m/s %s\nCAPE: %.0f J/kg | CIN: %.0f J/kg\nHelicity: %.0f m²/s² | Lapse: %.1f K/km\nTornado Potential: %.0f%%",
        env.Temperature,
        env.DewPoint,
        env.Pressure,
        surfaceWind.Magnitude,
        directionText,
        stormMotion.Magnitude,
        stormMotionText,
        env.CAPE or self.Readouts.CAPE,
        env.CIN or self.Readouts.CIN,
        env.Helicity or self.Readouts.Helicity,
        env.LapseRate or 0,
        (env.TornadoPotential or self._atmosphere:ComputeTornadoPotential(position)) * 100
    )
end

function Instrumentation:Destroy()
    if self._connection then
        self._connection:Disconnect()
        self._connection = nil
    end
end

return Instrumentation
