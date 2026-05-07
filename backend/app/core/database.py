from collections.abc import Generator

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from app.core.config import get_settings

EMBEDDING_DIMENSIONS = 768


class Base(DeclarativeBase):
    pass


class UserFile(Base):
    __tablename__ = "user_files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    storage_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(40), default="processing")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunks: Mapped[list["ContentChunk"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("user_files.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    text: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(40))
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    start_seconds: Mapped[float | None] = mapped_column(nullable=True)
    end_seconds: Mapped[float | None] = mapped_column(nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))

    file: Mapped[UserFile] = relationship(back_populates="chunks")


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    if settings.database_url.startswith("postgresql"):
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

