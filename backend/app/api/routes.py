from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user, verify_token_string
from app.core.config import Settings, get_settings
from app.core.database import UserFile, get_db
from app.models.schemas import ChatRequest, ChatResponse, FileOut, SummaryResponse
from app.services.ai import AIProvider
from app.services.files import list_user_files, save_and_process_upload
from app.services.retrieval import answer_question

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/files", response_model=FileOut)
async def upload_file(
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> UserFile:
    if not (
        upload.content_type == "application/pdf"
        or (upload.content_type or "").startswith("audio/")
        or (upload.content_type or "").startswith("video/")
    ):
        raise HTTPException(status_code=400, detail="Upload a PDF, audio file, or video file.")
    return await save_and_process_upload(db=db, owner_id=user.uid, upload=upload, settings=settings)


@router.get("/files", response_model=list[FileOut])
def files(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[UserFile]:
    return list_user_files(db, user.uid)


@router.get("/files/{file_id}/summary", response_model=SummaryResponse)
def summary(
    file_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> SummaryResponse:
    row = db.get(UserFile, file_id)
    if not row or row.owner_id != user.uid:
        raise HTTPException(status_code=404, detail="File not found")
    return SummaryResponse(file_id=row.id, summary=row.summary or "Summary is not available yet.")


@router.get("/files/{file_id}/content")
def file_content(
    file_id: int,
    token: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    user = verify_token_string(token, settings)
    row = db.get(UserFile, file_id)
    if not row or row.owner_id != user.uid:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=row.storage_path, media_type=row.content_type, filename=row.filename)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    answer, sources = await answer_question(
        db=db,
        owner_id=user.uid,
        question=request.question,
        file_id=request.file_id,
        ai=AIProvider(settings),
    )
    return ChatResponse(answer=answer, sources=sources)
