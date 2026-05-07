from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.database import UserFile
from app.services import files
from app.services.chunker import RawChunk


class FakeDb:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, item):
        self.added.append(item)
        if isinstance(item, UserFile):
            item.id = 7

    def commit(self):
        self.commits += 1

    def refresh(self, item):
        return None


class FakeUpload:
    filename = "demo.pdf"
    content_type = "application/pdf"

    async def read(self):
        return b"%PDF"


@pytest.mark.asyncio
async def test_save_and_process_upload(monkeypatch, tmp_path):
    class FakeAi:
        def __init__(self, settings):
            pass

        async def embed(self, text):
            return [0.0] * 768

        async def embed_many(self, texts):
            return [[0.0] * 768 for _ in texts]

        async def summarize(self, text):
            return "summary"

    monkeypatch.setattr(files, "extract_chunks", fake_extract_chunks)
    monkeypatch.setattr(files, "AIProvider", FakeAi)

    db = FakeDb()
    row = await files.save_and_process_upload(
        db=db,
        owner_id="user",
        upload=FakeUpload(),
        settings=Settings(upload_dir=tmp_path),
    )

    assert row.id == 7
    assert row.status == "ready"
    assert row.summary == "summary"
    assert len(db.added) == 2
    assert db.commits == 2


@pytest.mark.asyncio
async def test_save_and_process_upload_marks_failed(monkeypatch, tmp_path):
    async def fail_extract(path, content_type, settings):
        raise RuntimeError("boom")

    monkeypatch.setattr(files, "extract_chunks", fail_extract)
    db = FakeDb()

    with pytest.raises(RuntimeError):
        await files.save_and_process_upload(
            db=db,
            owner_id="user",
            upload=FakeUpload(),
            settings=Settings(upload_dir=tmp_path),
        )

    assert db.added[0].status == "failed"


@pytest.mark.asyncio
async def test_extract_chunks_rejects_unsupported(tmp_path):
    with pytest.raises(ValueError):
        await files.extract_chunks(tmp_path / "demo.txt", "text/plain", Settings())


@pytest.mark.asyncio
async def test_extract_chunks_uses_pdf_parser(monkeypatch, tmp_path):
    monkeypatch.setattr(files, "extract_pdf_chunks", lambda path: [RawChunk("pdf", "pdf")])

    chunks = await files.extract_chunks(tmp_path / "demo.pdf", "application/pdf", Settings())

    assert chunks[0].text == "pdf"


@pytest.mark.asyncio
async def test_extract_chunks_uses_transcription(monkeypatch, tmp_path):
    class FakeTranscriber:
        def __init__(self, settings):
            pass

        async def transcribe(self, path, content_type):
            return [{"text": "media", "start": 1, "end": 2}]

    monkeypatch.setattr(files, "TranscriptionProvider", FakeTranscriber)

    chunks = await files.extract_chunks(Path("demo.mp4"), "video/mp4", Settings())

    assert chunks[0].start_seconds == 1


async def fake_extract_chunks(path, content_type, settings):
    return [RawChunk(text="chunk", source_type="pdf", page_number=1)]

