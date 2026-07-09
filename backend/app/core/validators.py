from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BeforeValidator


def validate_cnpj(value: str) -> str:
    """
    Valida se o valor é um CNPJ válido, e retorna apenas os dígitos.

    Args:
        value (str): O valor do CNPJ a ser validado.
    Returns:
        str: Os dígitos do CNPJ se for válido.
    Raises:
        ValueError: Se o valor não for um CNPJ válido.
    """

    digits = "".join(filter(str.isdigit, value))

    if len(digits) != 14:
        raise ValueError("CNPJ deve conter 14 dígitos.")

    if len(set(digits)) == 1:
        raise ValueError("CNPJ inválido.")

    def calc_digit(digits: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(digits, weights, strict=False))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    if calc_digit(digits[:12], weights_1) != int(digits[12]):
        raise ValueError("CNPJ inválido.")

    if calc_digit(digits[:13], weights_2) != int(digits[13]):
        raise ValueError("CNPJ inválido.")

    return digits


def validate_cpf(value: str) -> str:
    """
    Valida se o valor é um CPF válido, e retorna apenas os dígitos.

    Args:
        value (str): O valor do CPF a ser validado.
    Returns:
        str: Os dígitos do CPF se for válido.
    Raises:
        ValueError: Se o valor não for um CPF válido.
    """

    digits = "".join(filter(str.isdigit, value))

    if len(digits) != 11:
        raise ValueError("CPF deve conter 11 dígitos.")

    if len(set(digits)) == 1:
        raise ValueError("CPF inválido.")

    def calc_digit(digits: str, weight: int) -> int:
        total = sum(
            int(d) * w for d, w in zip(digits, range(weight, 1, -1), strict=False)
        )
        remainder = (total * 10) % 11
        return 0 if remainder == 10 else remainder

    if calc_digit(digits[:9], weight=10) != int(digits[9]):
        raise ValueError("CPF inválido.")

    if calc_digit(digits[:10], weight=11) != int(digits[10]):
        raise ValueError("CPF inválido.")

    return digits


def validate_cnpj_or_cpf(value: str) -> str:
    """
    Valida se o valor é um CNPJ ou CPF válido, e retorna apenas os dígitos.

    Args:
        value (str): O valor do CNPJ ou CPF a ser validado.
    Returns:
        str: Os dígitos do CNPJ ou CPF se for válido.
    Raises:
        ValueError: Se o valor não for um CNPJ ou CPF válido.
    """

    digits = "".join(filter(str.isdigit, value))

    if len(digits) == 14:
        return validate_cnpj(value)
    if len(digits) == 11:
        return validate_cpf(value)
    raise ValueError("Valor deve ser um CNPJ ou CPF válido.")


def validate_timezone(value: str) -> str:
    """
    Valida se o valor é um timezone IANA válido.

    Args:
        value (str): O valor do timezone a ser validado.
    Returns:
        str: O valor do timezone se for válido.
    Raises:
        ValueError: Se o valor não for um timezone IANA válido.
    """

    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as e:
        raise ValueError(
            f"Timezone inválida: '{value}'. Use um timezone IANA válido."
        ) from e

    return value


Cnpj = Annotated[str, BeforeValidator(validate_cnpj)]
Cpf = Annotated[str, BeforeValidator(validate_cpf)]
CnpjOrCpf = Annotated[str, BeforeValidator(validate_cnpj_or_cpf)]
Timezone = Annotated[str, BeforeValidator(validate_timezone)]
