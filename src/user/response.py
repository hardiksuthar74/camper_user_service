from pydantic import BaseModel, EmailStr


# 📤 Response schema for /auth/login
class EmailVerifyResponse(BaseModel):
    email: EmailStr
    verified: bool
    registered: bool


# 📤 Response schema for /auth/verify-otp
class VerifyOtpResponse(BaseModel):
    email: EmailStr
    verified: bool
    message: str
    access_token: str | None = None
    refresh_token: str | None = None


class UserCreateResponse(BaseModel):
    first_name: str
    last_name: str
