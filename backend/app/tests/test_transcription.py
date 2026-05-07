import pytest

from app.core.config import Settings
from app.services import transcription
from app.services.transcription import TranscriptionProvider


@pytest.mark.asyncio
async def test_transcription_provider_returns_dev_segment_without_key(tmp_path):
    media = tmp_path / "sample.mp3"
    media.write_bytes(b"not really audio")

    segments = await TranscriptionProvider(Settings(deepgram_api_key=None)).transcribe(media, "audio/mpeg")

    assert segments[0]["start"] == 0.0
    assert "Deepgram API key" in segments[0]["text"]


@pytest.mark.asyncio
async def test_transcription_provider_parses_utterances(monkeypatch, tmp_path):
    media = tmp_path / "sample.mp3"
    media.write_bytes(b"audio")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": {
                    "utterances": [
                        {"transcript": "hello", "start": 1.0, "end": 2.0},
                    ]
                }
            }

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, params, headers, content):
            assert headers["Authorization"] == "Token key"
            assert content == b"audio"
            return FakeResponse()

    monkeypatch.setattr(transcription.httpx, "AsyncClient", FakeClient)

    segments = await TranscriptionProvider(Settings(deepgram_api_key="key")).transcribe(
        media, "audio/mpeg"
    )

    assert segments == [{"text": "hello", "start": 1.0, "end": 2.0}]


@pytest.mark.asyncio
async def test_transcription_provider_parses_channel_transcript(monkeypatch, tmp_path):
    media = tmp_path / "sample.mp3"
    media.write_bytes(b"audio")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": {
                    "channels": [{"alternatives": [{"transcript": "fallback transcript"}]}]
                }
            }

    class FakeClient:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, params, headers, content):
            return FakeResponse()

    monkeypatch.setattr(transcription.httpx, "AsyncClient", FakeClient)

    segments = await TranscriptionProvider(Settings(deepgram_api_key="key")).transcribe(
        media, "audio/mpeg"
    )

    assert segments == [{"text": "fallback transcript", "start": 0.0, "end": 0.0}]

