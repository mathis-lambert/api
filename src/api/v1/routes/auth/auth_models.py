from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel


class ApiKeyEntry(BaseModel):
    api_key: str
    user_id: str
    created_at: datetime
    expires_at: Optional[Union[datetime, None]] = None


class GetTokenRequestBody(BaseModel):
    username: str
    password: str
    expires_in: int = 30


class GetTokenResponse(BaseModel):
    access_token: str
    token_type: str


class GetApiKeyRequestBody(BaseModel):
    expires_in: Optional[Union[int, None]] = None


class GetApiKeyResponse(BaseModel):
    api_key: str
    expires_at: str | None


class RegisterRequestBody(BaseModel):
    username: str
    email: str
    password: str


class RegisterResponse(BaseModel):
    msg: str
    user: dict


class LogoutResponse(BaseModel):
    msg: str


class VerifyResponse(BaseModel):
    msg: str
    user: dict
