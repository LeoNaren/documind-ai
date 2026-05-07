from pathlib import Path

from pypdf import PdfReader

from app.services.chunker import RawChunk, chunk_text


def extract_pdf_chunks(path: Path) -> list[RawChunk]:
    reader = PdfReader(str(path))
    chunks: list[RawChunk] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chunks.extend(chunk_text(text, source_type="pdf", page_number=index))
    return chunks

