from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from src.api.deps import CurrentUser, DbSession
from src.core.security import create_access_token, decode_access_token, hash_password, verify_password
from src.core.token_blacklist import token_blacklist
from src.models.user import User
from src.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse

router = APIRouter()

# 简单的登录频率限制缓存（生产环境建议使用 Redis）
_login_attempts: dict[str, list[datetime]] = {}


def _check_rate_limit(key: str, max_attempts: int = 5, window_seconds: int = 60) -> None:
    now = datetime.now(timezone.utc)
    attempts = _login_attempts.get(key, [])
    attempts = [t for t in attempts if (now - t).total_seconds() < window_seconds]
    _login_attempts[key] = attempts
    if len(attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试过于频繁，请稍后再试",
        )


def _record_attempt(key: str) -> None:
    attempts = _login_attempts.get(key, [])
    attempts.append(datetime.now(timezone.utc))
    _login_attempts[key] = attempts


@router.post("/register", response_model=AuthResponse)
async def register(data: RegisterRequest, db: DbSession) -> AuthResponse:
    # 邮箱格式校验
    if "@" not in data.email or len(data.email) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱格式不正确",
        )
    if len(data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少 6 位",
        )
    if not data.name or len(data.name.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="姓名不能为空",
        )

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )

    user = User(
        email=data.email,
        name=data.name.strip(),
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.flush()

    token = create_access_token(user.id)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        token=token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, request: Request, db: DbSession) -> AuthResponse:
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{data.email}"
    _check_rate_limit(rate_key)

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        _record_attempt(rate_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    token = create_access_token(user.id)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        token=token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request) -> None:
    # 将当前 token 加入黑名单，防止登出后被重放
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_access_token(token)
        if payload:
            token_blacklist.add(token, payload)
    return None
