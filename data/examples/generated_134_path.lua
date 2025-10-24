local PathfindingService = game:GetService("PathfindingService")

local function PathHelper134(startPos, endPos)
    local agentParameters = {
        AgentRadius = 4,
        AgentHeight = 5,
        AgentCanJump = true,
    }
    local path = PathfindingService:CreatePath(agentParameters)
    path:ComputeAsync(startPos, endPos)
    if path.Status ~= Enum.PathStatus.Success then
        return nil
    end
    return path:GetWaypoints()
end

return PathHelper134
