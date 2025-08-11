# routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from jose import jwt
from typing import Optional
import httpx
import os

router = APIRouter()

# GOOGLE CONFIG
GOOGLE_CLIENT_ID = "772276055253-kcv9pt3pdnbh35k7s87igqi9met85ear.apps.googleusercontent.com"
GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"

# Request body
class GoogleAuthRequest(BaseModel):
    credential: str

# Response (customize as needed)
class UserResponse(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None
    is_new_user: bool

# Load and cache Google certs (to verify token signature)
async def get_google_certs():
    async with httpx.AsyncClient() as client:
        response = await client.get(GOOGLE_CERTS_URL)
        response.raise_for_status()
        return response.json()["keys"]

# Google token verification
async def verify_google_token(token: str):
    from jose import jwt

    # Fetch Google's public certs
    certs = await get_google_certs()

    # Try verifying with all certs
    for cert in certs:
        try:
            payload = jwt.decode(
                token,
                cert,
                algorithms=["RS256"],
                audience=GOOGLE_CLIENT_ID,
                options={"verify_exp": True}
            )
            return payload
        except jwt.JWTError:
            continue

    raise HTTPException(status_code=401, detail="Invalid Google token")

# Main route
@router.post("/auth/google", response_model=UserResponse)
async def google_auth(data: GoogleAuthRequest):
    payload = await verify_google_token(data.credential)

    # Extract user info
    email = payload.get("email")
    name = payload.get("name")
    picture = payload.get("picture")

    # TODO: Replace with real DB call
    # For now, assume all users are new
    is_new_user = True

    return UserResponse(
        email=email,
        name=name,
        picture=picture,
        is_new_user=is_new_user
    )