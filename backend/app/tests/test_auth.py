import pytest
from fastapi import HTTPException

from app.core import auth
from app.core.auth import get_current_user, verify_token_string
from app.core.config import Settings


def test_verify_token_allows_dev_token_when_mock_auth_enabled():
    user = verify_token_string("dev-token", Settings(allow_mock_auth=True))

    assert user.uid == "dev-user"


def test_verify_token_rejects_missing_token():
    with pytest.raises(HTTPException):
        verify_token_string(None, Settings(allow_mock_auth=True))


@pytest.mark.asyncio
async def test_get_current_user_uses_mock_without_credentials():
    user = await get_current_user(None, Settings(allow_mock_auth=True))

    assert user.uid == "dev-user"


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_credentials_when_mock_disabled():
    with pytest.raises(HTTPException):
        await get_current_user(None, Settings(allow_mock_auth=False))


@pytest.mark.asyncio
async def test_get_current_user_accepts_dev_token_after_failed_firebase():
    credentials = type("Credentials", (), {"credentials": "dev-token"})()

    user = await get_current_user(credentials, Settings(allow_mock_auth=True))

    assert user.email == "dev@documind.local"


@pytest.mark.asyncio
async def test_get_current_user_rejects_bad_token():
    credentials = type("Credentials", (), {"credentials": "bad-token"})()

    with pytest.raises(HTTPException):
        await get_current_user(credentials, Settings(allow_mock_auth=True))


def test_verify_token_string_uses_firebase(monkeypatch):
    monkeypatch.setattr(auth, "_ensure_firebase", lambda settings: None)
    monkeypatch.setattr(
        auth.firebase_auth,
        "verify_id_token",
        lambda token: {"uid": "firebase-user", "email": "person@example.com"},
    )

    user = verify_token_string("real-token", Settings(allow_mock_auth=False))

    assert user.uid == "firebase-user"
    assert user.email == "person@example.com"


def test_ensure_firebase_requires_credentials():
    with pytest.raises(RuntimeError):
        auth._ensure_firebase(Settings(allow_mock_auth=False))
