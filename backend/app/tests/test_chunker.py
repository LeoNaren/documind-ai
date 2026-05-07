from app.services.chunker import chunk_text, chunk_transcript_segments


def test_chunk_text_keeps_page_metadata():
    chunks = chunk_text("A sentence. " * 200, source_type="pdf", page_number=3, max_chars=200)

    assert len(chunks) > 1
    assert {chunk.page_number for chunk in chunks} == {3}
    assert {chunk.source_type for chunk in chunks} == {"pdf"}


def test_chunk_text_returns_empty_for_blank_input():
    assert chunk_text("   \n", source_type="pdf") == []


def test_chunk_transcript_segments_groups_timestamps():
    chunks = chunk_transcript_segments(
        [
            {"text": "intro", "start": 0.0, "end": 1.5},
            {"text": "main topic", "start": 1.5, "end": 4.0},
        ],
        max_chars=100,
    )

    assert len(chunks) == 1
    assert chunks[0].text == "intro main topic"
    assert chunks[0].start_seconds == 0.0
    assert chunks[0].end_seconds == 4.0


def test_chunk_transcript_segments_flushes_when_large():
    chunks = chunk_transcript_segments(
        [
            {"text": "a" * 20, "start": 0, "end": 1},
            {"text": "b" * 20, "start": 1, "end": 2},
        ],
        max_chars=10,
    )

    assert len(chunks) == 2
    assert chunks[0].start_seconds == 0
    assert chunks[1].start_seconds == 1
