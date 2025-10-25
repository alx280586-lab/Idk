from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from .highlights import HighlightCandidate


ASPECT_RATIO_DIMENSIONS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
}


def generate_clip_assets(
    candidates: List[HighlightCandidate],
    auto_subtitles: bool,
    include_emojis: bool,
    include_captions: bool,
    aspect_ratios: List[str],
    target_platforms: List[str],
) -> List[Dict[str, object]]:
    clips: List[Dict[str, object]] = []
    for candidate in candidates:
        clip_id = str(uuid4())
        for aspect_ratio in aspect_ratios:
            resolution = ASPECT_RATIO_DIMENSIONS.get(aspect_ratio, (1080, 1920))
            clips.append(
                {
                    "clip_id": clip_id,
                    "start": candidate["start"],
                    "end": candidate["end"],
                    "duration": candidate["end"] - candidate["start"],
                    "aspect_ratio": aspect_ratio,
                    "resolution": {
                        "width": resolution[0],
                        "height": resolution[1],
                    },
                    "platforms": target_platforms,
                    "subtitles": auto_subtitles,
                    "emojis": include_emojis,
                    "captions": include_captions,
                    "caption_text": candidate["text"],
                    "thumbnail": f"https://placehold.co/{resolution[0]}x{resolution[1]}?text=Clip",
                }
            )
    return clips
