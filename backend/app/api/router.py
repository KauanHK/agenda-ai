from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_establishment_actor
from app.modules.auth.api.router import router as auth_router
from app.modules.booking.adapters.http.dependencies import ServiceKeyDep
from app.modules.booking.adapters.http.router import router as booking_router
from app.modules.clients.api.router import router as clients_router
from app.modules.dashboard.api.router import router as dashboard_router
from app.modules.establishments.api.router import router as establishments_router
from app.modules.memberships.api.router import router as memberships_router
from app.modules.memberships.api.router import user_router as memberships_user_router
from app.modules.messaging_templates.api.router import (
    router as messaging_templates_router,
)
from app.modules.operating_hours.api.router import router as operating_hours_router
from app.modules.scheduling_notifications.api.router import (
    router as scheduling_notifications_router,
)
from app.modules.schedulings.api.router import router as schedulings_router
from app.modules.services.api.router import router as services_router
from app.modules.unavailabilities.api.router import router as unavailabilities_router
from app.modules.users.api.router import router as users_router


def build_messaging_router() -> APIRouter:
    """Constrói o router para as funcionalidades de mensagens."""

    router = APIRouter(prefix="/messaging")

    router.include_router(
        messaging_templates_router,
        prefix="/templates",
        tags=["Messaging Templates"],
    )

    router.include_router(
        scheduling_notifications_router,
        prefix="/notifications",
        tags=["Scheduling Notifications"],
    )

    return router


def build_establishment_router() -> APIRouter:
    """Contrói o router para as funcionalidades relacionadas a um estabelecimento específico."""

    router = APIRouter(
        prefix="/establishments/{establishment_id}",
        dependencies=[Depends(get_current_establishment_actor)],
    )

    router.include_router(
        operating_hours_router, prefix="/operating-hours", tags=["Operating Hours"]
    )

    router.include_router(build_messaging_router())
    router.include_router(clients_router, prefix="/clients", tags=["Clients"])
    router.include_router(services_router, prefix="/services", tags=["Services"])
    router.include_router(
        memberships_router, prefix="/members", tags=["Establishment Members"]
    )

    router.include_router(
        schedulings_router, prefix="/schedulings", tags=["Schedulings"]
    )

    router.include_router(
        unavailabilities_router, prefix="/unavailabilities", tags=["Unavailabilities"]
    )

    router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
    return router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(auth_router, prefix="/auth", tags=["Auth"])
    router.include_router(users_router, prefix="/users", tags=["Users"])
    router.include_router(
        memberships_user_router, prefix="/users", tags=["My Memberships"]
    )

    router.include_router(
        establishments_router, prefix="/establishments", tags=["Establishments"]
    )

    # Canal automático (WhatsApp): máquina-a-máquina, autenticado por chave de serviço
    # em vez do JWT do painel.
    router.include_router(
        booking_router,
        prefix="/agent",
        tags=["Agent"],
        dependencies=[ServiceKeyDep],
    )

    router.include_router(build_establishment_router())
    return router


api_router = build_api_router()
