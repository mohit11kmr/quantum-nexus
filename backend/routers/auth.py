"""Auth routes."""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from services.auth_service import (
    register_user,
    authenticate_user,
    get_user_by_username,
    get_current_user,
    auth_manager,
)

router = APIRouter()


@router.post("/api/auth/register")
def auth_register(payload: Dict[str, Any]):
    user = register_user(
        username=payload.get("username", ""),
        email=payload.get("email", ""),
        password=payload.get("password", ""),
        full_name=payload.get("full_name", ""),
    )
    access = auth_manager.create_access_token({"sub": user["username"], "role": user["role"]})
    refresh = auth_manager.create_refresh_token({"sub": user["username"]})
    return {"user": user, "access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/api/auth/login")
def auth_login(payload: Dict[str, Any]):
    user = authenticate_user(payload.get("username", ""), payload.get("password", ""))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access = auth_manager.create_access_token({"sub": user["username"], "role": user["role"]})
    refresh = auth_manager.create_refresh_token({"sub": user["username"]})
    return {"user": user, "access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/api/auth/refresh")
def auth_refresh(payload: Dict[str, Any]):
    token = payload.get("refresh_token", "")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    decoded = auth_manager.decode_token(token, expected_type="refresh")
    user = get_user_by_username(str(decoded.get("sub", "")))
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    access = auth_manager.create_access_token({"sub": user["username"], "role": user["role"]})
    return {"user": user, "access_token": access, "token_type": "bearer"}


@router.get("/api/auth/me")
def auth_me(current_user: Dict = Depends(get_current_user)):
    return current_user
