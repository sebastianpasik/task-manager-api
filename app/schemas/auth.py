from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, SecretStr


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
