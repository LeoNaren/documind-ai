from dataclasses import dataclass

import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.core.config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    uid: str
    email: str | None = None


def _ensure_firebase(settings: Settings) -> None:
    if firebase_admin._apps:
        return
    if not (
        settings.firebase_project_id
        and settings.firebase_client_email
        and settings.firebase_private_key
    ):
        raise RuntimeError("Firebase service account environment variables are not configured")

    private_key = settings.firebase_private_key.replace("\\n", "\n")
    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "client_email": settings.firebase_client_email,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )
    firebase_admin.initialize_app(cred)


async def get_current_user(
    credentials_: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if credentials_ is None:
        if settings.allow_mock_auth:
            return CurrentUser(uid="dev-user", email="dev@documind.local")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = credentials_.credentials
    try:
        _ensure_firebase(settings)
        decoded = firebase_auth.verify_id_token(token)
    except Exception as exc:
        if settings.allow_mock_auth and token == "dev-token":
            return CurrentUser(uid="dev-user", email="dev@documind.local")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(exc)}",
        ) from exc

    return CurrentUser(uid=decoded["uid"], email=decoded.get("email"))


def verify_token_string(token: str | None, settings: Settings) -> CurrentUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        _ensure_firebase(settings)
        decoded = firebase_auth.verify_id_token(token)
    except Exception as exc:
        if settings.allow_mock_auth and token == "dev-token":
            return CurrentUser(uid="dev-user", email="dev@documind.local")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(exc)}",
        ) from exc
    return CurrentUser(uid=decoded["uid"], email=decoded.get("email"))
