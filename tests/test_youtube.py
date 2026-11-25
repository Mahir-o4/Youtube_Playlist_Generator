from __future__ import annotations

from services.youtube import YouTubeClient


def test_no_language_or_region_bias_by_default(monkeypatch) -> None:
    client = YouTubeClient(api_key="fake")
    assert client.region_code == ""
    captured: dict = {}

    def fake_request(endpoint: str, params: dict) -> dict:
        captured.update(params)
        return {"items": []}

    monkeypatch.setattr(client, "_request", fake_request)
    client.search("vectors")
    assert "regionCode" not in captured
    assert "relevanceLanguage" not in captured
    assert captured["type"] == "video"


def test_region_can_be_restricted(monkeypatch) -> None:
    monkeypatch.setenv("YOUTUBE_REGION_CODE", "IN")
    client = YouTubeClient(api_key="fake")
    assert client.region_code == "IN"
    captured: dict = {}

    def fake_request(endpoint: str, params: dict) -> dict:
        captured.update(params)
        return {"items": []}

    monkeypatch.setattr(client, "_request", fake_request)
    client.search("vectors")
    assert captured["regionCode"] == "IN"
    assert "relevanceLanguage" not in captured
