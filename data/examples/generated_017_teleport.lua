local Players = game:GetService("Players")

local function TeleportHelper017(playerName, destination)
    local player = Players:FindFirstChild(playerName)
    if not player or not player.Character then
        return false
    end
    local root = player.Character:FindFirstChild("HumanoidRootPart")
    if root then
        root.CFrame = destination.CFrame
        return true
    end
    return false
end

return TeleportHelper017
