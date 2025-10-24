local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function RemoteHelper138(eventName, ...)
    local remote = ReplicatedStorage:FindFirstChild(eventName)
    if remote and remote.IsA and remote:IsA("RemoteEvent") then
        remote:FireServer(...)
        return true
    end
    return false
end

return RemoteHelper138
