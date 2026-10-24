from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_in: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    existing_user = await user_repository.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    hashed_pwd = hash_password(user_in.password)
    new_user = await user_repository.create(
        db=db,
        email=user_in.email,
        hashed_password=hashed_pwd,
        role=user_in.role,
        name=user_in.name or user_in.email.split("@")[0],
    )
    return new_user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(credentials: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    user = await user_repository.get_by_email(db, email=credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token_endpoint(
    refresh_in: TokenRefreshRequest, db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(refresh_in.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id_str: str | None = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    user = await user_repository.get_by_id(db, user_id=user_id)

    if not user or not user.is_active:
        raise credentials_exception

    new_access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
    )
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_200_OK, summary="User logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"detail": "Successfully logged out."}


@router.get("/me", response_model=UserResponse, summary="Get current logged in user")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
