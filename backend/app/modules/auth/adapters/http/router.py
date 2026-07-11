from fastapi import APIRouter, status

from app.api.deps.auth import ActorDep
from app.modules.auth.adapters.http.dependencies import (
    AuthLoginDep,
    AuthRefreshDep,
    UsersCreatorDep,
)
from app.modules.auth.adapters.http.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.modules.auth.application.dtos.commands import LoginCommand, RefreshCommand
from app.modules.users.adapters.http.schemas import UserCreate, UserRead
from app.modules.users.application.dtos.commands import CreateUserCommand

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    creator: UsersCreatorDep,
    actor: ActorDep,
) -> UserRead:
    command = CreateUserCommand(**data.model_dump(exclude_unset=True))
    user = await creator.create(command, actor)
    return UserRead.model_validate(user.to_dict())


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    auth: AuthLoginDep,
) -> TokenResponse:
    token_pair = await auth.login(
        LoginCommand(username=data.username, password=data.password)
    )
    return TokenResponse.model_validate(token_pair.to_dict())


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    auth: AuthRefreshDep,
) -> TokenResponse:
    token_pair = await auth.refresh(RefreshCommand(refresh_token=data.refresh_token))
    return TokenResponse.model_validate(token_pair.to_dict())
