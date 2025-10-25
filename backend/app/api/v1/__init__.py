from fastapi import APIRouter

from . import analytics, automation, scheduling, trends, video

api_router = APIRouter()
api_router.include_router(video.router, prefix="/videos", tags=["videos"])
api_router.include_router(scheduling.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(trends.router, prefix="/trends", tags=["trends"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])

__all__ = [
    "api_router",
    "analytics",
    "automation",
    "scheduling",
    "trends",
    "video",
]
