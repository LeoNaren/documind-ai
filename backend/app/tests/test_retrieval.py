import pytest

from app.core.database import ContentChunk
from app.services.retrieval import answer_question


class FakeAi:
    async def embed(self, question):
        return [0.0] * 768

    async def answer(self, question, contexts):
        assert contexts == ["source text"]
        return "answer"


class FakeDb:
    def execute(self, statement):
        chunk = ContentChunk(
            file_id=1,
            owner_id="user",
            text="source text",
            source_type="media",
            start_seconds=3.0,
            end_seconds=5.0,
            embedding=[0.0] * 768,
        )
        return type("Rows", (), {"all": lambda self: [(chunk, "demo.mp4")]})()


@pytest.mark.asyncio
async def test_answer_question_returns_sources():
    answer, sources = await answer_question(
        db=FakeDb(),
        owner_id="user",
        question="question",
        file_id=1,
        ai=FakeAi(),
    )

    assert answer == "answer"
    assert sources[0].filename == "demo.mp4"
    assert sources[0].start_seconds == 3.0
