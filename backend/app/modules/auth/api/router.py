from fastapi import APIRouter, status

from app.api.deps import ActorDep
from app.modules.auth.api.deps import (
    AuthLoginDep,
    AuthRefreshDep,
    UsersCreatorDep,
)
from app.modules.auth.domain.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.modules.users.domain.schemas import UserCreate, UserRead

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    creator: UsersCreatorDep,
    actor: ActorDep,
) -> UserRead:
    return await creator.create(data, actor)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    auth: AuthLoginDep,
) -> TokenResponse:
    return await auth.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    auth: AuthRefreshDep,
) -> TokenResponse:
    return await auth.refresh(data)
