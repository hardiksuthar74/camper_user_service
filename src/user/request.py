from pydantic import BaseModel, EmailStr, Field


class EmailVerifyRequest(BaseModel):
    email: EmailStr


# 📥 Request schema for /auth/verify-otp
class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
