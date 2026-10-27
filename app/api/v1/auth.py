from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import refresh_token_repository
from app.repositories.user_repository import user_repository
from app.schemas.user import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserLogoutRequest,
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
    refresh_token, jti, expire = create_refresh_token(data={"sub": str(user.id)})
    token_hash = hash_token(refresh_token)
    await refresh_token_repository.create_token(
        db,
        user_id=user.id,
        token_hash=token_hash,
        jti=jti,
        expires_at=expire,
    )
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
        jti: str | None = payload.get("jti")
        if not user_id_str:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    user = await user_repository.get_by_id(db, user_id=user_id)

    if not user or not user.is_active:
        raise credentials_exception

    token_hash = hash_token(refresh_in.refresh_token)
    token_record = None
    if jti:
        token_record = await refresh_token_repository.get_by_jti(db, jti=jti)
    if not token_record:
        token_record = await refresh_token_repository.get_by_token_hash(
            db, token_hash=token_hash
        )

    if not token_record:
        raise credentials_exception

    if token_record.revoked_at is not None:
        await refresh_token_repository.revoke_all_for_user(db, user_id=user.id)
        raise credentials_exception

    if token_record.expires_at <= datetime.now(UTC):
        raise credentials_exception

    await refresh_token_repository.revoke(db, refresh_token=token_record)

    new_access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
    )
    new_refresh_token, new_jti, new_expire = create_refresh_token(
        data={"sub": str(user.id)}
    )
    new_token_hash = hash_token(new_refresh_token)
    await refresh_token_repository.create_token(
        db,
        user_id=user.id,
        token_hash=new_token_hash,
        jti=new_jti,
        expires_at=new_expire,
    )
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_200_OK, summary="User logout")
async def logout(
    logout_in: UserLogoutRequest | None = None,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if logout_in and logout_in.refresh_token:
        try:
            payload = decode_token(logout_in.refresh_token)
            jti = payload.get("jti")
            token_hash = hash_token(logout_in.refresh_token)
            token_record = None
            if jti:
                token_record = await refresh_token_repository.get_by_jti(db, jti=jti)
            if not token_record:
                token_record = await refresh_token_repository.get_by_token_hash(
                    db, token_hash=token_hash
                )
            if token_record and token_record.revoked_at is None:
                await refresh_token_repository.revoke(db, refresh_token=token_record)
        except Exception:
            pass
    elif current_user:
        await refresh_token_repository.revoke_all_for_user(db, user_id=current_user.id)

    return {"detail": "Successfully logged out."}


@router.get("/me", response_model=UserResponse, summary="Get current logged in user")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

