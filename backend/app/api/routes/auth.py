# backend/app/api/routes/auth.py

import httpx
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import create_access_token, get_current_user
from app.models.user import User

router   = APIRouter()
settings = get_settings()

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"
REDIRECT_URI     = "http://localhost:8000/api/v1/auth/callback"


@router.get("/auth/login")
async def login():
    """Redirect user to Google OAuth login page."""
    params = {
        "client_id"    : settings.GOOGLE_CLIENT_ID,
        "redirect_uri" : REDIRECT_URI,
        "response_type": "code",
        "scope"        : "openid email profile",
        "access_type"  : "offline",
        "prompt"       : "consent"
    }
    query  = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/auth/callback")
async def auth_callback(code: str, db: AsyncSession = Depends(get_db)):# pragma: no cover
    """Handle Google OAuth callback — exchange code for user info."""

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code"         : code,
                "client_id"    : settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri" : REDIRECT_URI,
                "grant_type"   : "authorization_code"
            }
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    token_data   = token_response.json()
    access_token = token_data.get("access_token")

    # Get user info from Google
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            GOOGLE_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")

    google_user = user_response.json()

    # Find or create user in DB
    result = await db.execute(
        select(User).where(User.google_id == google_user["id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        # New user — create account
        user = User(
            google_id  = google_user["id"],
            email      = google_user["email"],
            full_name  = google_user.get("name"),
            avatar_url = google_user.get("picture"),
            is_active  = True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Existing user — update info
        user.full_name  = google_user.get("name")
        user.avatar_url = google_user.get("picture")
        await db.commit()

    # Create JWT token
    jwt_token = create_access_token({"sub": str(user.id)})

    # Redirect to frontend with token
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}"
    )


@router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):# pragma: no cover
    """Get current authenticated user info."""
    return {
        "id"        : str(current_user.id),
        "email"     : current_user.email,
        "full_name" : current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "is_active" : current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


@router.post("/auth/logout")
async def logout():
    """Logout — frontend should delete the token."""
    return {"message": "Logged out successfully. Please delete your token."}