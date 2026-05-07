import pytest
from fastapi import HTTPException

from app.api import routes
from app.core.auth import CurrentUser
from app.core.config import Settings
from app.core.database import UserFile
from app.models.schemas import ChatRequest


class FakeDb:
    def __init__(self, row=None):
        self.row = row

    def get(self, model, file_id):
        return self.row


@pytest.mark.asyncio
async def test_upload_file_rejects_unsupported():
    upload = type("Upload", (), {"content_type": "text/plain"})()

    with pytest.raises(HTTPException):
        await routes.upload_file(
            upload=upload,
            db=FakeDb(),
            user=CurrentUser(uid="user"),
            settings=Settings(),
        )


@pytest.mark.asyncio
async def test_upload_file_uses_service(monkeypatch):
    async def fake_save_and_process_upload(db, owner_id, upload, settings):
        return UserFile(
            id=1,
            owner_id=owner_id,
            filename="demo.pdf",
            content_type="application/pdf",
            storage_path="demo.pdf",
            status="ready",
        )

    monkeypatch.setattr(routes, "save_and_process_upload", fake_save_and_process_upload)
    upload = type("Upload", (), {"content_type": "application/pdf"})()

    row = await routes.upload_file(
        upload=upload,
        db=FakeDb(),
        user=CurrentUser(uid="user"),
        settings=Settings(),
    )

    assert row.filename == "demo.pdf"


def test_files_route(monkeypatch):
    monkeypatch.setattr(routes, "list_user_files", lambda db, owner_id: ["file"])

    assert routes.files(FakeDb(), CurrentUser(uid="user")) == ["file"]


def test_summary_route_rejects_missing_file():
    with pytest.raises(HTTPException):
        routes.summary(1, FakeDb(), CurrentUser(uid="user"))


def test_summary_route_returns_summary():
    row = UserFile(
        id=1,
        owner_id="user",
        filename="demo.pdf",
        content_type="application/pdf",
        storage_path="demo.pdf",
        status="ready",
        summary="summary",
    )

    response = routes.summary(1, FakeDb(row), CurrentUser(uid="user"))

    assert response.summary == "summary"


def test_file_content_rejects_wrong_owner(tmp_path):
    row = UserFile(
        id=1,
        owner_id="other",
        filename="demo.pdf",
        content_type="application/pdf",
        storage_path=str(tmp_path / "demo.pdf"),
        status="ready",
    )

    with pytest.raises(HTTPException):
        routes.file_content(1, "dev-token", FakeDb(row), Settings(allow_mock_auth=True))


@pytest.mark.asyncio
async def test_chat_route(monkeypatch):
    async def fake_answer_question(db, owner_id, question, file_id, ai):
        return "answer", []

    monkeypatch.setattr(routes, "answer_question", fake_answer_question)

    response = await routes.chat(
        ChatRequest(question="q"),
        db=FakeDb(),
        user=CurrentUser(uid="user"),
        settings=Settings(),
    )

    assert response.answer == "answer"

