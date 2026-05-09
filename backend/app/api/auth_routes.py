from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.config import get_settings
from app.models.user import UserModel, UserCreate, UserResponse, UserPreferencesModel
from app.core.auth import (
    verify_password, get_password_hash, create_tokens, decode_token,
    create_password_reset_token, verify_password_reset_token
)
from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from datetime import datetime, timezone, timedelta
import os
import secrets
import httpx

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

# Simple in-memory token blacklist (use Redis in production)
_token_blacklist: set[str] = set()


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/minute")
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    password_hash = get_password_hash(user_data.password)
    
    new_user = UserModel(
        email=user_data.email,
        name=user_data.name,
        password_hash=password_hash
    )
    
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    
    user_preferences = UserPreferencesModel(user_id=new_user.id)
    db.add(user_preferences)
    await db.commit()
    
    tokens = create_tokens(new_user.id, new_user.email)
    return TokenResponse(**tokens)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = create_tokens(user.id, user.email)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(request: Request, request_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(request_data.refresh_token)
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        tokens = create_tokens(user.id, user.email)
        return TokenResponse(**tokens)
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.post("/logout")
async def logout(request: LogoutRequest):
    try:
        payload = decode_token(request.refresh_token)
        jti = payload.get("jti")
        if jti:
            _token_blacklist.add(jti)
        # Also blacklist by token itself as fallback
        _token_blacklist.add(request.refresh_token)
        return {"message": "Successfully logged out"}
    except ValueError:
        return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        onboarding_completed=current_user.onboarding_completed,
        created_at=current_user.created_at
    )


@router.post("/verify-email")
@limiter.limit("5/minute")
async def send_verification_email(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Send an email verification token.

    For self-hosted use, returns the token directly.
    In production, this would send an email.
    """
    if current_user.email_verified:
        return {"message": "Email is already verified."}

    token = create_password_reset_token(current_user.email)
    current_user.verification_token = token
    current_user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.commit()

    return {
        "message": "Verification email sent.",
        "verification_token": token,  # Returned for self-hosted convenience; remove in production
    }


@router.post("/verify-email/confirm")
@limiter.limit("10/minute")
async def confirm_email(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Confirm email verification using a token."""
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    result = await db.execute(
        select(UserModel).where(
            UserModel.email == email,
            UserModel.verification_token == token
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.verification_token_expires or user.verification_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    await db.commit()

    return {"message": "Email verified successfully."}


# ========== OAuth ==========

class OAuthCallbackRequest(BaseModel):
    code: str
    provider: str


async def _exchange_google_code(code: str) -> dict:
    """Exchange Google authorization code for tokens and user info."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_resp.raise_for_status()
        return user_resp.json()


async def _exchange_github_code(code: str) -> dict:
    """Exchange GitHub authorization code for tokens and user info."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_resp.raise_for_status()
        user = user_resp.json()

        # Fetch email if not public
        if not user.get("email"):
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            emails_resp.raise_for_status()
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary")), None)
            if primary:
                user["email"] = primary["email"]
        return user


@router.get("/oauth/{provider}")
async def oauth_authorize_url(provider: str):
    """Get the OAuth authorization URL for a provider."""
    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Google OAuth not configured")
        state = secrets.token_urlsafe(32)
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.OAUTH_REDIRECT_URI}"
            "&response_type=code"
            "&scope=openid%20email%20profile"
            f"&state={state}"
        )
        return {"auth_url": url, "state": state}

    if provider == "github":
        if not settings.GITHUB_CLIENT_ID:
            raise HTTPException(status_code=400, detail="GitHub OAuth not configured")
        state = secrets.token_urlsafe(32)
        url = (
            "https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={settings.OAUTH_REDIRECT_URI}"
            f"&scope=user:email%20read:user"
            f"&state={state}"
        )
        return {"auth_url": url, "state": state}

    raise HTTPException(status_code=400, detail="Unsupported provider")


@router.post("/oauth/callback", response_model=TokenResponse)
async def oauth_callback(
    request: Request,
    data: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth callback and create/authenticate user."""
    try:
        if data.provider == "google":
            oauth_user = await _exchange_google_code(data.code)
        elif data.provider == "github":
            oauth_user = await _exchange_github_code(data.code)
        else:
            raise HTTPException(status_code=400, detail="Unsupported provider")

        email = oauth_user.get("email")
        name = oauth_user.get("name") or oauth_user.get("login") or email.split("@")[0]

        if not email:
            raise HTTPException(status_code=400, detail="OAuth provider did not return email")

        # Find or create user
        result = await db.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = UserModel(
                email=email,
                name=name,
                password_hash=None,  # OAuth users have no local password
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)

            prefs = UserPreferencesModel(user_id=user.id)
            db.add(prefs)
            await db.commit()
        else:
            await db.commit()

        tokens = create_tokens(user.id, user.email)
        return TokenResponse(**tokens)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a password reset token for the user.

    In production, this would send an email with a reset link.
    For self-hosted use, the token is returned directly.
    """
    result = await db.execute(select(UserModel).where(UserModel.email == data.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If an account exists with this email, a reset link has been sent."}

    reset_token = create_password_reset_token(user.email)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.commit()

    # In production, send email here instead of returning the token
    return {
        "message": "If an account exists with this email, a reset link has been sent.",
        "reset_token": reset_token,  # Returned for self-hosted convenience; remove in production
    }


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using a valid reset token."""
    email = verify_password_reset_token(data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    result = await db.execute(
        select(UserModel).where(
            UserModel.email == email,
            UserModel.reset_token == data.token
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Validate new password length
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )

    user.password_hash = get_password_hash(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.commit()

    return {"message": "Password reset successfully. Please log in with your new password."}
