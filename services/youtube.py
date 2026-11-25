"""YouTube Data API client with disk-cached responses."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

from schemas import VideoCandidate

_API_ROOT = "https://www.googleapis.com/youtube/v3"
_ROOT = Path(__file__).resolve().parents[1]
_ENV_PATH = _ROOT / ".env"
_CACHE_DIR = _ROOT / "data" / "cache"
_DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def _as_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _parse_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = _DURATION_RE.fullmatch(value)
    if not match:
        return None
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


class YouTubeClient:
    """Minimal REST client for search.list + videos.list."""

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int | None = None,
        finalists: int | None = None,
    ) -> None:
        load_dotenv(_ENV_PATH)
        load_dotenv(Path.cwd() / ".env")
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "YouTube API key missing. Set YOUTUBE_API_KEY in .env or the environment."
            )
        self.max_results = max_results or int(os.getenv("YOUTUBE_SEARCH_RESULTS", "20"))
        self.finalists = finalists or int(os.getenv("YOUTUBE_FINALISTS", "5"))
        self.region_code = os.getenv("YOUTUBE_REGION_CODE", "").strip()
        self._cache_dir = _CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._http = httpx.Client(timeout=30)

    def _request(self, endpoint: str, params: dict) -> dict:
        digest_source = json.dumps({"endpoint": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha256(digest_source.encode()).hexdigest()[:20]
        cache_path = self._cache_dir / f"{endpoint}_{digest}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response = self._http.get(
            f"{_API_ROOT}/{endpoint}",
            params={**params, "key": self.api_key},
        )
        if response.status_code != 200:
            try:
                message = response.json().get("error", {}).get("message", "")
            except ValueError:
                message = ""
            raise RuntimeError(
                f"YouTube API {endpoint} failed ({response.status_code}): "
                f"{message or response.text[:200]}"
            )
        data = response.json()
        cache_path.write_text(json.dumps(data), encoding="utf-8")
        return data

    def search(self, query: str) -> list[tuple[str, dict]]:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": self.max_results,
            "order": "relevance",
        }
        if self.region_code:
            params["regionCode"] = self.region_code
        data = self._request("search", params)
        return [
            (item["id"]["videoId"], item["snippet"])
            for item in data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

    def videos(self, video_ids: list[str]) -> list[dict]:
        details: list[dict] = []
        for start in range(0, len(video_ids), 50):
            batch = video_ids[start : start + 50]
            data = self._request(
                "videos",
                {
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(batch),
                },
            )
            details.extend(data.get("items", []))
        return details

    def candidates_for_query(self, query: str, unit_key: str) -> list[VideoCandidate]:
        hits = self.search(query)
        if not hits:
            return []
        details = {item["id"]: item for item in self.videos([vid for vid, _ in hits])}

        candidates: list[VideoCandidate] = []
        for video_id, search_snippet in hits:
            item = details.get(video_id)
            if not item:
                continue
            snippet = item.get("snippet", {}) or search_snippet
            thumbnails = snippet.get("thumbnails", {})
            thumbnail = (
                thumbnails.get("medium")
                or thumbnails.get("high")
                or thumbnails.get("default")
                or {}
            ).get("url", "")
            stats = item.get("statistics", {})
            candidates.append(
                VideoCandidate(
                    video_id=video_id,
                    unit_key=unit_key,
                    search_query=query,
                    title=snippet.get("title", ""),
                    channel=snippet.get("channelTitle", ""),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    thumbnail=thumbnail,
                    duration_seconds=_parse_duration(
                        (item.get("contentDetails", {}) or {}).get("duration")
                    ),
                    views=_as_int(stats.get("viewCount")),
                    likes=_as_int(stats.get("likeCount")),
                    comments=_as_int(stats.get("commentCount")),
                )
            )
        return candidates
