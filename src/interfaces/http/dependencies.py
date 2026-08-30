"""Acesso tipado ao container montado no lifespan da aplicação."""

from typing import Annotated

from fastapi import Depends, Request

from src.container import Container


def get_container(request: Request) -> Container:
    """Devolve o `Container` guardado em `app.state` pelo lifespan."""
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]
