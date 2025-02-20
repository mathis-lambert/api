from pydantic import BaseModel


class GetTokenRequestBody(BaseModel):
    username: str
    password: str
    expires_in: int = 30


class GetTokenResponse(BaseModel):
    access_token: str
    token_type: str


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
