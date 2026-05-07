from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import ContentChunk, UserFile
from app.services.ai import AIProvider
from app.services.chunker import RawChunk, chunk_transcript_segments
from app.services.pdf_parser import extract_pdf_chunks
from app.services.transcription import TranscriptionProvider


async def save_and_process_upload(
    *,
    db: Session,
    owner_id: str,
    upload: UploadFile,
    settings: Settings,
) -> UserFile:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.filename or "upload.bin").name
    storage_path = settings.upload_dir / f"{uuid4().hex}-{safe_name}"
    storage_path.write_bytes(await upload.read())

    file_row = UserFile(
        owner_id=owner_id,
        filename=safe_name,
        content_type=upload.content_type or "application/octet-stream",
        storage_path=str(storage_path),
    )
    db.add(file_row)
    db.commit()
    db.refresh(file_row)

    try:
        raw_chunks = await extract_chunks(storage_path, file_row.content_type, settings)
        ai = AIProvider(settings)

        embeddings = await ai.embed_many([raw.text for raw in raw_chunks])
        for idx, raw in enumerate(raw_chunks):
            db.add(
                ContentChunk(
                    file_id=file_row.id,
                    owner_id=owner_id,
                    text=raw.text,
                    source_type=raw.source_type,
                    page_number=raw.page_number,
                    start_seconds=raw.start_seconds,
                    end_seconds=raw.end_seconds,
                    embedding=embeddings[idx],
                )
            )
        file_row.summary = await ai.summarize("\n\n".join(chunk.text for chunk in raw_chunks)[:20000])
        file_row.status = "ready"
    except Exception:
        file_row.status = "failed"
        raise
    finally:
        db.commit()
        db.refresh(file_row)

    return file_row


async def extract_chunks(path: Path, content_type: str, settings: Settings) -> list[RawChunk]:
    if content_type == "application/pdf" or path.suffix.lower() == ".pdf":
        return extract_pdf_chunks(path)
    if content_type.startswith("audio/") or content_type.startswith("video/"):
        segments = await TranscriptionProvider(settings).transcribe(path, content_type)
        return chunk_transcript_segments(segments)
    raise ValueError("Unsupported file type. Upload a PDF, audio file, or video file.")


def list_user_files(db: Session, owner_id: str) -> list[UserFile]:
    return list(db.scalars(select(UserFile).where(UserFile.owner_id == owner_id).order_by(UserFile.id.desc())))

