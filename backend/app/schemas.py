from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    display_name: str = Field(min_length=1, max_length=128)
    email: str | None = None
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("用户名不能为空")
        return cleaned

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("显示名称不能为空")
        return cleaned


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class PatternWrite(BaseModel):
    name: str = Field(min_length=1, max_length=512)
    original_title: str | None = None
    motif_type: str = Field(default="其他", max_length=64)
    secondary: str | None = None
    dynasty: str = Field(default="年代未定", max_length=64)
    date_text: str | None = None
    century: str | None = None
    carrier: str = Field(default="其他", max_length=64)
    description: str | None = None
    source: str = Field(default="手工录入", max_length=64)
    source_id: str | None = None
    source_url: str | None = None
    license: str | None = None
    status: str = Field(default="confirmed", max_length=32)
    annotator: str | None = None
    notes: str | None = None
    dataset_origin: str | None = "后台编目"
    has_image: bool = False
    label_valid: bool = True
    image_url: str | None = None


class PatternPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=512)
    original_title: str | None = None
    motif_type: str | None = Field(default=None, max_length=64)
    secondary: str | None = None
    dynasty: str | None = Field(default=None, max_length=64)
    date_text: str | None = None
    century: str | None = None
    carrier: str | None = Field(default=None, max_length=64)
    description: str | None = None
    source: str | None = Field(default=None, max_length=64)
    source_url: str | None = None
    license: str | None = None
    status: str | None = Field(default=None, max_length=32)
    annotator: str | None = None
    notes: str | None = None
    dataset_origin: str | None = None
    has_image: bool | None = None
    label_valid: bool | None = None
    image_url: str | None = None


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    display_name: str = Field(min_length=1, max_length=128)
    email: str | None = None
    password: str = Field(min_length=6, max_length=128)
    is_admin: bool = False
    is_active: bool = True


class UserPatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    email: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
    is_admin: bool | None = None
    is_active: bool | None = None

