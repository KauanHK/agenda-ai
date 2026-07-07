from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Gera um hash seguro para a senha fornecida usando o algoritmo bcrypt.

    Args:
        password (str): A senha em texto plano a ser hashada.

    Returns:
        str: O hash da senha gerado.
    """

    return pwd_context.hash(
        secret=password.encode("utf-8")[:72],
    )


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica se a senha fornecida corresponde ao hash fornecido.

    Args:
        password (str): A senha em texto plano a ser verificada.
        password_hash (str): O hash da senha a ser comparado.

    Returns:
        bool: True se a senha corresponder ao hash, False caso contrário.
    """

    return pwd_context.verify(
        secret=password.encode("utf-8")[:72],
        hash=password_hash,
    )
