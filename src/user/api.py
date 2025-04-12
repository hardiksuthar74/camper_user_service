from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Header, status
import jwt
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.request import EmailVerifyRequest, UserCreateRequest, VerifyOtpRequest
from src.user.response import EmailVerifyResponse, UserCreateResponse, VerifyOtpResponse

from src.db.manager.manager import db_manager

from src.user.model import User


from src.utils.generate_otp import generate_otp
from src.utils.redis_cache import redis_client
from src.utils.send_otp_email import send_otp_email

user_router = APIRouter()

session = Depends(db_manager.get_db_session)

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


async def get_current_user(Authorization: str = Header(...)):
    if not Authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
        )

    token = Authorization.split(" ")[1]

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials: no subject in token",
            )

        email: str = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials: no subject in token",
            )
        return email
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
        )


def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


@user_router.post(
    "/auth/login",
    response_model=EmailVerifyResponse,
)
async def login(
    body: EmailVerifyRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = session,
):
    # Check if user already exists
    get_user_by_email_query = select(User).where(User.email == body.email)
    result = await session.execute(get_user_by_email_query)
    user_data = result.scalars().first()

    # If user doesn't exist, insert new user
    if not user_data:
        insert_user_stmt = insert(User).values(**body.model_dump()).returning(User)
        result = await session.execute(insert_user_stmt)
        user_data = result.scalars().first()

        if user_data:
            await session.refresh(user_data)

    # notification service will be called
    # send otp logic
    otp = generate_otp()
    await redis_client.setex(body.email, 600, otp)  # Store OTP
    await redis_client.setex(f"{body.email}:tries", 600, 0)  # Track OTP attempts

    # Queue email to be sent in background
    background_tasks.add_task(send_otp_email, body.email, otp)

    return EmailVerifyResponse(
        email=body.email,
        verified=user_data.email_verified if user_data else False,
        registered=user_data.registerd if user_data else False,
    )


@user_router.post("/auth/verify-otp", response_model=VerifyOtpResponse)
async def verify_otp(
    body: VerifyOtpRequest,
    session: AsyncSession = session,
):
    expected_otp = await redis_client.get(body.email)

    if not expected_otp:
        return VerifyOtpResponse(
            email=body.email,
            verified=False,
            message="OTP expired or not found.",
        )

    # Check attempt count
    tries_key = f"{body.email}:tries"
    tries = await redis_client.get(tries_key)

    if tries is not None and int(tries) >= 5:
        return VerifyOtpResponse(
            email=body.email,
            verified=False,
            message="Too many incorrect attempts. Please request a new OTP.",
        )

    if body.otp != expected_otp:
        await redis_client.incr(tries_key)

        return VerifyOtpResponse(
            email=body.email,
            verified=False,
            message="Invalid OTP.",
        )

    # If OTP is correct, mark user as verified
    query = select(User).where(User.email == body.email)
    result = await session.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.email_verified = True
    await session.commit()
    await session.refresh(user)

    # Clear OTP after successful verification
    await redis_client.delete(body.email)
    await redis_client.delete(tries_key)

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    return VerifyOtpResponse(
        email=body.email,
        verified=True,
        message="Email verified successfully.",
        access_token=access_token,
        refresh_token=refresh_token,
    )


@user_router.get("/profile")
async def read_profile(current_user: str = Depends(get_current_user)):
    return {"email": current_user}


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise Exception("Not a refresh token")
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise Exception("Refresh token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid refresh token")


@user_router.post("/auth/refresh-token")
async def refresh_access_token(Authorization: str = Header(...)):
    if not Authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=400, detail="Invalid authorization header format"
        )

    refresh_token = Authorization.split(" ")[1]

    try:
        user_email = verify_refresh_token(refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    # Generate a new access token
    new_access_token = create_access_token({"sub": user_email})
    return {"access_token": new_access_token, "token_type": "bearer"}


@user_router.post(
    "/auth/register",
    response_model=UserCreateResponse,
)
async def register_user(
    body: UserCreateRequest,
    current_user: str = Depends(get_current_user),
    session: AsyncSession = session,
):
    query = select(User).where(User.email == current_user)

    result = await session.execute(query)

    user = result.scalars().one()

    if user:
        user.first_name = body.first_name
        user.last_name = body.last_name
        user.registerd = True

        await session.commit()
        await session.refresh(user)

        return UserCreateResponse(
            last_name=user.last_name,
            first_name=user.first_name,
        )
