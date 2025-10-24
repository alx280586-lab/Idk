local CollectionService = game:GetService("CollectionService")

local function SpawnHelper106(tagName)
    local candidates = CollectionService:GetTagged(tagName or "Beacon")
    if #candidates == 0 then
        warn("No spawn points tagged", tagName)
        return nil
    end
    local index = math.random(1, #candidates)
    local chosen = candidates[index]
    return chosen.Position
end

return SpawnHelper106
