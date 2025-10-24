local CollectionService = game:GetService("CollectionService")

local function SpawnHelper091(tagName)
    local candidates = CollectionService:GetTagged(tagName or "NPC")
    if #candidates == 0 then
        warn("No spawn points tagged", tagName)
        return nil
    end
    local index = math.random(1, #candidates)
    local chosen = candidates[index]
    return chosen.Position
end

return SpawnHelper091
