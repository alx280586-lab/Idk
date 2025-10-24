local TweenService = game:GetService("TweenService")

local function UiHelper060(guiObject, visible)
    if not guiObject then
        return
    end
    local goal = { Transparency = visible and 0 or 1 }
    local tweenInfo = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
    local tween = TweenService:Create(guiObject, tweenInfo, goal)
    tween:Play()
end

return UiHelper060
