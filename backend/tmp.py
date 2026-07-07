from app.core.security.passwords import hash_password
from app.db.session import db
from app.modules.users.domain.model import User
from app.modules.users.infra.repository import UsersRepository


async def create_user(session) -> None:
    repository = UsersRepository(session)

    user = User(
        name="Admin",
        email="kauankaestner06@gmail.com",
        password_hash=hash_password("admin123"),
        is_global_admin=True,
        is_active=True,
    )

    await repository.create(user)


async def main() -> None:

    db.init()
    try:
        async for session in db.session_context():
            await create_user(session)
            await session.commit()
    finally:
        await db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
