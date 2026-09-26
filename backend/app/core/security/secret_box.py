"""
Cifra simétrica dos segredos de canais (token do bot, segredo do webhook).

Usa Fernet com a `CHANNEL_SECRETS_KEY`. Os segredos precisam voltar em claro para
chamar a Bot API, então não dá para usar hash; a chave fica fora do banco, e um dump
da tabela sozinho não entrega os tokens.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.core.settings import settings


class SecretBoxKeyError(RuntimeError):
    """O texto cifrado não abre com a `CHANNEL_SECRETS_KEY` configurada."""


def encrypt(plaintext: str) -> str:
    """
    Cifra um segredo para gravar no banco.

    Args:
        plaintext (str): O segredo em claro.

    Returns:
        str: O token Fernet, em ASCII.
    """

    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """
    Decifra um segredo lido do banco.

    Args:
        ciphertext (str): O token Fernet gravado por `encrypt`.

    Returns:
        str: O segredo em claro.

    Raises:
        SecretBoxKeyError: Se a chave configurada não for a que cifrou o texto.
    """

    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        # Sem o texto cifrado na mensagem: ele não é segredo, mas não ajuda em nada.
        raise SecretBoxKeyError(
            "Chave de cifra não confere: a CHANNEL_SECRETS_KEY não é a que cifrou "
            "este segredo."
        ) from exc


def _fernet() -> Fernet:
    return Fernet(settings.CHANNEL_SECRETS_KEY)
