from pydantic import BaseModel


class FileOut(BaseModel):
    id: int
    filename: str
    content_type: str
    status: str
    summary: str | None = None

    model_config = {"from_attributes": True}


class SourceOut(BaseModel):
    file_id: int
    filename: str
    text: str
    page_number: int | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None


class ChatRequest(BaseModel):
    question: str
    file_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceOut]


class SummaryResponse(BaseModel):
    file_id: int
    summary: str

