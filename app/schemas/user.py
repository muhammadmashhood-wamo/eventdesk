import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.user import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None
    role: UserRole = UserRole.ATTENDEE

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str):
        if len(value) < 8:
            raise ValueError("Password must be 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain atleast one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain atleast one lowercase letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain atleast one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError(
                'Password must contain at least one special character (!@#$%^&*(),.?":{}|<>).'
            )
        return value

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: object) -> object:
        if isinstance(value, str):
            for member in UserRole:
                if member.value.lower() == value.lower() or member.name.lower() == value.lower():
                    return member
        return value

    @field_validator("role")
    @classmethod
    def prevent_admit_registration(cls, value: UserRole) -> UserRole:
        if value == UserRole.ADMIN:
            raise ValueError("Self-registration as Admin is not allowed.")
        return value


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    email: EmailStr | None = None
    name: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class UserPasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError(
                'Password must contain at least one special character (!@#$%^&*(),.?":{}|<>).'
            )
        return value


class UserAdminUpdateRequest(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: object) -> object:
        if isinstance(value, str):
            for member in UserRole:
                if member.value.lower() == value.lower() or member.name.lower() == value.lower():
                    return member
        return value


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    skip: int
    limit: int
