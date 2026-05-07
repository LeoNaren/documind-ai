import pytest

from app.core.config import Settings
from app.services.ai import AIProvider, _fit_dimensions, deterministic_embedding, mock_generate


def test_deterministic_embedding_shape_and_norm():
    embedding = deterministic_embedding("hello")

    assert len(embedding) == 768
    assert deterministic_embedding("hello") == embedding
    assert deterministic_embedding("other") != embedding


@pytest.mark.asyncio
async def test_ai_provider_uses_mock_without_key():
    provider = AIProvider(Settings(gemini_api_key=None))

    answer = await provider.answer("What is this?", ["A source"])

    assert "Gemini quota is unavailable" in answer


def test_mock_summary_prompt():
    response = mock_generate("Summarize this\n\nThis document explains uploads. It covers chat.")

    assert "This document explains uploads" in response


@pytest.mark.asyncio
async def test_ai_provider_uses_gemini_client():
    class FakeModels:
        async def embed_content(self, model, contents):
            assert model == "embedding-model"
            assert contents == "hello"
            return type("EmbedResult", (), {"embeddings": [type("Embedding", (), {"values": [1.0]})()]})()

        async def generate_content(self, model, contents):
            assert model == "chat-model"
            assert "hello" in contents
            return type("GenerateResult", (), {"text": "real answer"})()

    provider = AIProvider(Settings(gemini_api_key=None))
    provider.settings.gemini_chat_model = "chat-model"
    provider.settings.gemini_embedding_model = "embedding-model"
    provider._client = type("FakeClient", (), {"aio": type("Aio", (), {"models": FakeModels()})()})()

    assert await provider.embed("hello") == [1.0] + [0.0] * 767
    assert await provider.generate("hello") == "real answer"


@pytest.mark.asyncio
async def test_ai_provider_gemini_empty_text_fallback():
    class FakeModels:
        async def generate_content(self, model, contents):
            return type("GenerateResult", (), {"text": ""})()

    provider = AIProvider(Settings(gemini_api_key=None))
    provider._client = type("FakeClient", (), {"aio": type("Aio", (), {"models": FakeModels()})()})()

    assert await provider.generate("prompt") == "I could not generate a response."


def test_fit_dimensions_truncates_and_pads():
    assert _fit_dimensions([1.0, 2.0, 3.0], 2) == [1.0, 2.0]
    assert _fit_dimensions([1.0], 3) == [1.0, 0.0, 0.0]
