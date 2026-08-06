"""
JWT Authentication Service (multi-user).

Adopts the AuthManager pattern from trading_bot/src/infrastructure/auth.py
(PyJWT + bcrypt) and implements it cleanly with a JSON user store so the API
can support multiple users without a database dependency.
"""

import json
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional

import bcrypt
import jwt
from fastapi import HTTPException, Header, status

SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = 7

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def _load_users() -> Dict[str, Any]:
    if not USERS_FILE.exists():
        return {"users": {}}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": {}}


def _save_users(store: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


class AuthManager:
    def __init__(self, secret_key: str = SECRET_KEY):
        self.secret_key = secret_key
        self.algorithm = ALGORITHM

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            return False

    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str, expected_type: str = None) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")
        return payload

    def public_user(self, user: Dict) -> Dict:
        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at"),
        }


auth_manager = AuthManager()


def register_user(username: str, email: str, password: str, full_name: str = "") -> Dict:
    store = _load_users()
    users = store["users"]
    username = username.strip().lower()
    email = email.strip().lower()
    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="username, email and password are required")
    if username in users:
        raise HTTPException(status_code=409, detail="Username already taken")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = {
        "id": uuid.uuid4().hex,
        "username": username,
        "email": email,
        "full_name": full_name.strip(),
        "password_hash": auth_manager.hash_password(password),
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users[username] = user
    _save_users(store)
    return auth_manager.public_user(user)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    store = _load_users()
    user = store["users"].get(username.strip().lower())
    if not user:
        return None
    if not auth_manager.verify_password(password, user["password_hash"]):
        return None
    return auth_manager.public_user(user)


def get_user_by_username(username: str) -> Optional[Dict]:
    store = _load_users()
    user = store["users"].get(username.strip().lower())
    return auth_manager.public_user(user) if user else None


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """FastAPI dependency: require a valid Bearer access token."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

    payload = auth_manager.decode_token(token, expected_type="access")
    user = get_user_by_username(str(payload.get("sub", "")))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user
