local StormManager = require(script.Parent.StormManager)
local Instrumentation = require(script.Parent.Instrumentation)

local manager = StormManager.new({
    MaxStorms = 6,
    StormSpawnInterval = 60,
    MinimumPotential = 0.42,
    Atmosphere = {
        DomainSize = Vector2.new(22000, 22000),
        GridResolution = 16,
        DayLengthSeconds = 900,
        FrontStrength = 0.75,
        TerrainInfluence = 0.45,
    },
})

local instruments = Instrumentation.new(manager:GetAtmosphere())

local function describeStormState(storm, state)
    local ef = state.Tornado and state.Tornado:GetEFScale() or 0
    local descriptor = string.format(
        "Stage: %s | Intensity: %.2f | Updraft: %.0f m/s | Rotation: %.0f m/s | Hail: %.1f in | EF%d", 
        state.Stage,
        state.Intensity,
        state.UpdraftStrength,
        state.RotationStrength,
        state.HailSize,
        ef
    )
    return descriptor
end

manager.StormSpawned.Event:Connect(function(storm, env)
    print(string.format(
        "[StormFront] New storm seeded at %s | CAPE %.0f | Helicity %.0f | Potential %.0f%%",
        tostring(env.Position),
        env.CAPE,
        env.Helicity,
        manager:GetAtmosphere():ComputeTornadoPotential(env.Position) * 100
    ))
end)

manager.StormUpdated.Event:Connect(function(storm, state)
    if state.HasTornado then
        print(string.format(
            "[StormFront] Tornado EF%d | Damage %.0f%% | %s",
            state.Tornado:GetEFScale(),
            state.Tornado:GetDamageEstimate() * 100,
            describeStormState(storm, state)
        ))
    elseif state.Stage == "Supercell" or state.Stage == "Tornadogenesis" then
        print(string.format("[StormFront] Mesocyclone tightening | %s", describeStormState(storm, state)))
    end
end)

manager.StormDissipated.Event:Connect(function(storm, state)
    print(string.format(
        "[StormFront] Storm dissipated after %.0f min | Peak intensity %.2f",
        storm.Age / 60,
        state.PeakIntensity
    ))
end)

script.Destroying:Connect(function()
    instruments:Destroy()
    manager:Destroy()
end)

return {
    StormManager = manager,
    Instruments = instruments,
}
