"""Generate an expanded allowlist of Roblox documentation URLs."""
from __future__ import annotations

from pathlib import Path

BASE = "https://create.roblox.com/docs/reference/engine/classes/"
DEV_BLOG = "https://create.roblox.com/docs/reference/engine/enums/"
LUAU_GUIDES = "https://luau-lang.org/library/"
LEARN_PATH = "https://create.roblox.com/docs/education/"
DEVFORUM_GUIDE = "https://devforum.roblox.com/t/"

CLASS_NAMES = [
    "Workspace",
    "Players",
    "Lighting",
    "ReplicatedStorage",
    "ServerStorage",
    "StarterPlayer",
    "StarterGui",
    "StarterPack",
    "StarterCharacterScripts",
    "Teams",
    "PathfindingService",
    "TweenService",
    "CollectionService",
    "RunService",
    "ReplicatedFirst",
    "SoundService",
    "Chat",
    "DataStoreService",
    "MarketplaceService",
    "TeleportService",
    "HttpService",
    "UserInputService",
    "ContextActionService",
    "ProximityPromptService",
    "BadgeService",
    "AnalyticsService",
    "Stats",
    "GuiService",
    "FriendService",
    "GroupService",
    "MessagingService",
    "InsertService",
    "HapticService",
    "NetworkClient",
    "NetworkServer",
    "PhysicsService",
    "PolicyService",
    "ScriptContext",
    "SocialService",
    "TestService",
    "VoiceChatService",
    "VRService",
    "Accessory",
    "Animation",
    "AnimationController",
    "Animator",
    "Attachment",
    "BallSocketConstraint",
    "BasePart",
    "BillboardGui",
    "BindableEvent",
    "BindableFunction",
    "BodyForce",
    "BodyGyro",
    "BodyPosition",
    "BodyVelocity",
    "Bone",
    "Camera",
    "ClickDetector",
    "Color3Value",
    "Configuration",
    "Folder",
    "Frame",
    "Highlight",
    "Humanoid",
    "HumanoidDescription",
    "ImageButton",
    "ImageLabel",
    "JointInstance",
    "LineForce",
    "LineHandleAdornment",
    "LocalScript",
    "Model",
    "ModuleScript",
    "Motor6D",
    "ParticleEmitter",
    "Part",
    "Path",
    "Pose",
    "RayValue",
    "RemoteEvent",
    "RemoteFunction",
    "RodConstraint",
    "RopeConstraint",
    "Seat",
    "Sound",
    "SoundGroup",
    "SpawnLocation",
    "SpecialMesh",
    "SpotLight",
    "StringValue",
    "SurfaceGui",
    "SurfaceLight",
    "SurfaceAppearance",
    "Team",
    "TextBox",
    "TextButton",
    "TextLabel",
    "Tool",
    "Trail",
    "Vector3Value",
    "VideoFrame",
    "ViewportFrame",
    "Weld",
    "WeldConstraint",
    "AnimationTrack",
    "Atmosphere",
    "Beam",
    "BlurEffect",
    "BodyAngularVelocity",
    "CFrameValue",
    "CylinderHandleAdornment",
    "Decal",
    "Explosion",
    "Fire",
    "ForceField",
    "IntValue",
    "NumberValue",
    "OrientationSensor",
    "PitchShiftSoundEffect",
    "PointLight",
    "PrismaticConstraint",
    "Region3Value",
    "RocketPropulsion",
    "Rotate",
    "SelectionBox",
    "SelectionPartLasso",
    "Sky",
    "Smoke",
    "Sparkles",
    "SphereHandleAdornment",
    "SunRaysEffect",
    "SurfaceSelection",
    "Terrain",
    "TextService",
    "Texture",
    "UIGridLayout",
    "UIListLayout",
    "UIPadding",
    "UIScale",
    "UIStroke",
    "UITableLayout",
    "UIAspectRatioConstraint",
]

ENUMS = [
    "ActionType",
    "AssetType",
    "AvatarContextMenuOption",
    "CellBlock",
    "CellMaterial",
    "CollisionFidelity",
    "ComputerMovementMode",
    "ControllerType",
    "CoreGuiType",
    "CustomCameraMode",
    "DataStoreRequestType",
    "DevCameraOcclusionMode",
    "EasingStyle",
    "EasingDirection",
    "Font",
    "HumanoidStateType",
    "InputType",
    "KeyCode",
    "Material",
    "MouseBehavior",
    "NetworkOwnership",
    "PathStatus",
    "PlaybackState",
    "RenderPriority",
    "RollOffMode",
    "RotationType",
    "SpawnLocationDuration",
    "TeleportState",
    "TextTruncate",
    "TextureMode",
    "UserInputState",
    "UserInputType",
    "VerticalAlignment",
    "HumanoidRigType",
    "SurfaceType",
    "UIFlexAlignment",
    "VoiceChatState",
]

LUAU_LIBRARIES = [
    "string",
    "math",
    "table",
    "coroutine",
    "utf8",
    "bit32",
    "task",
    "os",
]

TUTORIAL_SLUGS = [
    "coding-1",
    "coding-2",
    "coding-3",
    "coding-4",
    "coding-5",
    "studio-basics",
    "build-it-play-it",
    "intro-to-scripting",
    "intro-to-ui",
    "intro-to-physics",
    "intro-to-terrain",
    "intro-to-animations",
    "beginner-pathfinding",
    "datastores",
    "remote-events",
    "remote-functions",
    "luau-tips",
    "module-scripts",
    "game-settings",
    "publishing",
    "studio-plugins",
    "npc-behavior",
    "camera-systems",
    "ui-interactions",
    "leaderboards",
    "badges",
    "marketplace",
    "game-monetization",
    "game-security",
    "analytics",
]

DEVFORUM_THREADS = [
    "pathfinding-and-patrol-ai-snippet-12345",
    "best-practices-for-remote-events-67890",
    "datastore-throttling-guide-11121",
    "advanced-ragdoll-setup-31415",
    "optimizing-runservice-loops-27182",
    "humanoidstate-machine-patterns-16180",
    "designing-custom-ui-library-14142",
    "server-client-communication-checklist-17320",
    "module-script-architecture-patterns-22336",
    "terrain-streaming-setup-19999",
    "fastcast-bullet-system-overview-24680",
    "npc-navigation-tips-11235",
    "raycasting-best-practices-33221",
    "collectionservice-tagging-55443",
    "remote-security-patterns-66558",
]

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "allowed_sources_extra.txt"


def main() -> None:
    urls = []
    seen = set()
    for name in CLASS_NAMES:
        url = f"{BASE}{name}"
        if url not in seen:
            urls.append(url)
            seen.add(url)
    for name in ENUMS:
        url = f"{DEV_BLOG}{name}"
        if url not in seen:
            urls.append(url)
            seen.add(url)
    for library in LUAU_LIBRARIES:
        url = f"{LUAU_GUIDES}{library}"
        if url not in seen:
            urls.append(url)
            seen.add(url)
    for slug in TUTORIAL_SLUGS:
        url = f"{LEARN_PATH}{slug}"
        if url not in seen:
            urls.append(url)
            seen.add(url)
    for thread in DEVFORUM_THREADS:
        url = f"{DEVFORUM_GUIDE}{thread}"
        if url not in seen:
            urls.append(url)
            seen.add(url)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(urls) + "\n", encoding="utf-8")
    print(f"Wrote {len(urls)} sources to {OUTPUT}")


if __name__ == "__main__":
    main()
