"""
Cria o primeiro usuário admin global do sistema.

O backend não tem rota pública de cadastro: criar usuário via `POST /api/auth`
exige um ator já autenticado que seja admin global. Este script resolve o
problema do ovo e da galinha, inserindo o primeiro admin direto no banco.

Uso na VPS (stack de produção no ar):

    docker compose exec api uv run --no-sync python -m scripts.create_admin

Localmente:

    cd backend
    uv run python -m scripts.create_admin

Sem argumentos o script pergunta nome, e-mail, telefone (opcional) e senha de
forma interativa. Os valores também podem vir por flag ou variável de ambiente
(útil para provisionamento automatizado):

    python -m scripts.create_admin \
        --name "Fulana de Tal" \
        --email admin@exemplo.com \
        --phone "+5547999998888"

A senha nunca é lida por flag. No modo não interativo, informe-a pela variável
de ambiente ADMIN_PASSWORD.

Por segurança, o script se recusa a rodar quando já existe algum admin global;
passe --force para criar outro assim mesmo. E-mail e telefone precisam ser
únicos no banco.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from typing import NoReturn

import sqlalchemy as sa
from pydantic import TypeAdapter, ValidationError
from pydantic.networks import EmailStr

# Registra todos os models no metadata da Base antes de qualquer flush
# (o mapper de User referencia "Membership" via relationship string).
import app.db.models  # noqa: F401
from app.core.db.session import db
from app.core.phone import normalize_phone
from app.core.security.passwords import hash_password
from app.modules.users.adapters.db.models import User as UserModel
from app.modules.users.adapters.db.unit_of_work import UsersUnitOfWork
from app.modules.users.domain.entities import NewUser

MIN_PASSWORD_LENGTH = 8
MAX_NAME_LENGTH = 255

_email_validator: TypeAdapter[str] = TypeAdapter(EmailStr)


class InputError(Exception):
    """Erro de validação de entrada fornecida pelo operador."""


def _fail(message: str) -> NoReturn:
    print(f"erro: {message}", file=sys.stderr)
    raise SystemExit(1)


def _prompt(label: str, *, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{label}{suffix}: ").strip()
    except EOFError:
        _fail(
            f"não foi possível ler '{label}' (stdin fechado). "
            "Rode em um terminal interativo ou informe o valor por flag."
        )
    return value or (default or "")


def _resolve_name(cli_value: str | None) -> str:
    name = (cli_value or os.getenv("ADMIN_NAME") or "").strip()
    if not name and sys.stdin.isatty():
        name = _prompt("Nome")
    if not name:
        raise InputError("nome é obrigatório.")
    if len(name) > MAX_NAME_LENGTH:
        raise InputError(f"nome deve ter no máximo {MAX_NAME_LENGTH} caracteres.")
    return name


def _resolve_email(cli_value: str | None) -> str:
    raw = (cli_value or os.getenv("ADMIN_EMAIL") or "").strip()
    if not raw and sys.stdin.isatty():
        raw = _prompt("E-mail")
    if not raw:
        raise InputError("e-mail é obrigatório.")
    try:
        return _email_validator.validate_python(raw)
    except ValidationError as e:
        raise InputError(f"e-mail inválido: {raw!r}") from e


def _resolve_phone(cli_value: str | None) -> str | None:
    raw = (cli_value or os.getenv("ADMIN_PHONE") or "").strip()
    if not raw and sys.stdin.isatty():
        raw = _prompt("Telefone (opcional)")
    if not raw:
        return None
    try:
        return normalize_phone(raw)
    except ValueError as e:
        raise InputError(str(e)) from e


def _resolve_password() -> str:
    env_password = os.getenv("ADMIN_PASSWORD")
    if env_password is not None:
        if len(env_password) < MIN_PASSWORD_LENGTH:
            raise InputError(
                f"ADMIN_PASSWORD deve ter ao menos {MIN_PASSWORD_LENGTH} caracteres."
            )
        return env_password

    if not sys.stdin.isatty():
        raise InputError(
            "sem terminal interativo: informe a senha pela variável ADMIN_PASSWORD."
        )

    password = getpass.getpass("Senha: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise InputError(f"senha deve ter ao menos {MIN_PASSWORD_LENGTH} caracteres.")
    if getpass.getpass("Confirme a senha: ") != password:
        raise InputError("as senhas não conferem.")
    return password


async def _create_admin(
    *,
    name: str,
    email: str,
    phone: str | None,
    password_hash: str,
    force: bool,
) -> None:
    db.init()
    try:
        async with UsersUnitOfWork(session_factory=db.create_session) as uow:
            session = uow.session

            existing_admin = await session.scalar(
                sa.select(UserModel.email)
                .where(UserModel.is_global_admin.is_(True))
                .limit(1)
            )
            if existing_admin and not force:
                _fail(
                    f"já existe um admin global ({existing_admin}). "
                    "Use --force para criar outro."
                )

            if await session.scalar(
                sa.select(UserModel.id).where(UserModel.email == email).limit(1)
            ):
                _fail(f"já existe um usuário com o e-mail {email!r}.")

            if phone and await session.scalar(
                sa.select(UserModel.id).where(UserModel.phone == phone).limit(1)
            ):
                _fail(f"já existe um usuário com o telefone {phone!r}.")

            created = await uow.users.create(
                NewUser(
                    name=name,
                    email=email,
                    password_hash=password_hash,
                    phone=phone,
                    is_global_admin=True,
                    is_active=True,
                )
            )

        print(f"admin global criado: {created.email} (id={created.id})")
    finally:
        await db.close()


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.create_admin",
        description="Cria o primeiro usuário admin global do sistema.",
    )
    parser.add_argument("--name", help="nome do admin (ou variável ADMIN_NAME)")
    parser.add_argument("--email", help="e-mail do admin (ou variável ADMIN_EMAIL)")
    parser.add_argument(
        "--phone",
        help="telefone do admin, opcional (ou variável ADMIN_PHONE)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="cria mesmo que já exista um admin global",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    try:
        name = _resolve_name(args.name)
        email = _resolve_email(args.email)
        phone = _resolve_phone(args.phone)
        password = _resolve_password()
    except InputError as e:
        _fail(str(e))

    asyncio.run(
        _create_admin(
            name=name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            force=args.force,
        )
    )


if __name__ == "__main__":
    main()
