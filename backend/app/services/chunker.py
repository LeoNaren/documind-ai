from dataclasses import dataclass


@dataclass(frozen=True)
class RawChunk:
    text: str
    source_type: str
    page_number: int | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None


def chunk_text(
    text: str,
    *,
    source_type: str,
    page_number: int | None = None,
    max_chars: int = 1200,
    overlap: int = 160,
) -> list[RawChunk]:
    clean = " ".join(text.split())
    if not clean:
        return []

    chunks: list[RawChunk] = []
    start = 0
    while start < len(clean):
        end = min(start + max_chars, len(clean))
        if end < len(clean):
            sentence_end = clean.rfind(". ", start, end)
            if sentence_end > start + max_chars // 2:
                end = sentence_end + 1
        chunks.append(
            RawChunk(text=clean[start:end].strip(), source_type=source_type, page_number=page_number)
        )
        if end == len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def chunk_transcript_segments(segments: list[dict], max_chars: int = 1200) -> list[RawChunk]:
    chunks: list[RawChunk] = []
    current: list[str] = []
    start_seconds: float | None = None
    end_seconds: float | None = None

    for segment in segments:
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        if start_seconds is None:
            start_seconds = float(segment.get("start", 0))
        end_seconds = float(segment.get("end", start_seconds))
        current.append(text)

        if len(" ".join(current)) >= max_chars:
            chunks.append(
                RawChunk(
                    text=" ".join(current),
                    source_type="media",
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                )
            )
            current = []
            start_seconds = None

    if current:
        chunks.append(
            RawChunk(
                text=" ".join(current),
                source_type="media",
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            )
        )
    return chunks

