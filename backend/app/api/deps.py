from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from app.database import get_db
from app.config import get_settings
from app.core.auth import decode_token, TokenData, is_token_blacklisted
from app.models.user import UserModel

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if is_token_blacklisted(token):
            raise credentials_exception
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, email=email)
    except ValueError:
        raise credentials_exception
    
    result = await db.execute(select(UserModel).where(UserModel.id == token_data.user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user
