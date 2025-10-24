local CollectionService = game:GetService("CollectionService")

local function pickRandomSpawn(spawnTag)
    local spawns = CollectionService:GetTagged(spawnTag)
    if #spawns == 0 then
        return nil
    end
    local choice = spawns[math.random(1, #spawns)]
    return choice.Position
end

return pickRandomSpawn
