"""Transcript fetching via youtube-transcript-api with disk caching."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

from schemas import TranscriptSegment

_ROOT = Path(__file__).resolve().parents[1]
_CACHE_DIR = _ROOT / "data" / "cache"


class TranscriptFetcher:
    """Return timestamped transcript segments, or None when unavailable."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir or _CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(
        self, video_id: str, languages: Sequence[str] = ("en", "hi")
    ) -> list[TranscriptSegment] | None:
        cache_path = self._cache_dir / f"transcript_{video_id}_{'-'.join(languages)}.json"
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            raw = payload.get("segments")
            if raw is None:
                return None
            return [TranscriptSegment.model_validate(item) for item in raw]

        try:
            fetched = YouTubeTranscriptApi().fetch(
                video_id, languages=list(languages)
            )
            segments = [
                TranscriptSegment(
                    video_id=video_id,
                    start=float(snippet.start),
                    duration=float(snippet.duration),
                    text=str(snippet.text),
                )
                for snippet in fetched
            ]
        except Exception:
            cache_path.write_text(
                json.dumps({"segments": None}), encoding="utf-8"
            )
            return None

        cache_path.write_text(
            json.dumps({"segments": [s.model_dump() for s in segments]}),
            encoding="utf-8",
        )
        return segments
