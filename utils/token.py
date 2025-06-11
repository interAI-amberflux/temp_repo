from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

# Dependency for FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Environment configs
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pass_default_if_not_set")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def decode_jwt_token(token: str) -> Optional[Dict[str, str]]:
    """Decode a JWT token and return user info or None"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("user_id")
        role: Optional[str] = payload.get("role")

        if not user_id or not role:
            return None

        return {"id": user_id, "role": role}
    except JWTError:
        return None


def extract_user_from_token(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    """Used with FastAPI Depends()"""
    user = decode_jwt_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token information",
        )
    return user


def get_user_from_token(request: Request) -> Optional[Dict[str, str]]:
    """Used in middleware (manual token extraction)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    return decode_jwt_token(token)
