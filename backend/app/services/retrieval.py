from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.database import ContentChunk, UserFile
from app.models.schemas import SourceOut
from app.services.ai import AIProvider


async def answer_question(
    *,
    db: Session,
    owner_id: str,
    question: str,
    file_id: int | None,
    ai: AIProvider,
) -> tuple[str, list[SourceOut]]:
    query_embedding = await ai.embed(question)
    statement: Select = (
        select(ContentChunk, UserFile.filename)
        .join(UserFile, UserFile.id == ContentChunk.file_id)
        .where(ContentChunk.owner_id == owner_id)
        .order_by(ContentChunk.embedding.cosine_distance(query_embedding))
        .limit(5)
    )
    if file_id:
        statement = statement.where(ContentChunk.file_id == file_id)

    rows = db.execute(statement).all()
    chunks = [row[0] for row in rows]
    answer = await ai.answer(question, [chunk.text for chunk in chunks])
    sources = [
        SourceOut(
            file_id=chunk.file_id,
            filename=filename,
            text=chunk.text[:500],
            page_number=chunk.page_number,
            start_seconds=chunk.start_seconds,
            end_seconds=chunk.end_seconds,
        )
        for chunk, filename in rows
    ]
    return answer, sources

