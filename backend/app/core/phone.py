"""
Normalização de telefone.

O telefone é o identificador do cliente no canal automático (WhatsApp), mas a coluna
`clients.phone` é texto livre — quem cadastra pelo painel digita `(47) 99999-8888`,
enquanto a Evolution API entrega `5547999998888`. Comparar as duas strings direto não
funciona, então toda busca por telefone passa por `phone_lookup_keys`, que gera as
variantes em dígitos puros de um mesmo número.

Números sem código de país são assumidos brasileiros — é o único mercado atendido.
"""

import re

_NON_DIGITS = re.compile(r"\D")

BR_COUNTRY_CODE = "55"

# DDD (2) + 8 dígitos (fixo) ou 9 dígitos (celular)
_NATIONAL_LENGTHS = (10, 11)


def only_digits(raw: str) -> str:
    """
    Remove tudo que não for dígito.

    Args:
        raw (str): O telefone em qualquer formato.

    Returns:
        str: Apenas os dígitos do telefone.
    """

    return _NON_DIGITS.sub("", raw)


def normalize_phone(raw: str) -> str:
    """
    Converte um telefone para o formato canônico E.164 (`+5547999998888`).

    Usado ao gravar um telefone novo, para que os clientes criados pelo canal
    automático fiquem todos no mesmo formato.

    Args:
        raw (str): O telefone em qualquer formato.

    Returns:
        str: O telefone em E.164.

    Raises:
        ValueError: Se não sobrar nenhum dígito ou o número for curto demais.
    """

    digits = only_digits(raw)

    if len(digits) in _NATIONAL_LENGTHS:
        digits = BR_COUNTRY_CODE + digits

    if len(digits) < 10:
        raise ValueError(f"Telefone inválido: {raw!r}")

    return f"+{digits}"


def phone_lookup_keys(raw: str) -> list[str]:
    """
    Gera as variantes em dígitos puros pelas quais um telefone pode estar gravado.

    Cobre as duas ambiguidades reais da base: presença ou ausência do código do país,
    e presença ou ausência do nono dígito dos celulares brasileiros (números antigos
    foram cadastrados com 8 dígitos).

    Args:
        raw (str): O telefone em qualquer formato.

    Returns:
        list[str]:
            As variantes a procurar, sem duplicatas. Lista vazia se `raw` não tiver
            dígitos.
    """

    digits = only_digits(raw)
    if not digits:
        return []

    if digits.startswith(BR_COUNTRY_CODE) and len(digits) > max(_NATIONAL_LENGTHS):
        national = digits.removeprefix(BR_COUNTRY_CODE)
    else:
        national = digits

    nationals = {national}

    # celular com nono dígito -> também procura a forma antiga, de 8 dígitos
    if len(national) == 11 and national[2] == "9":
        nationals.add(national[:2] + national[3:])

    # número de 8 dígitos -> também procura a forma atual, com o 9
    if len(national) == 10:
        nationals.add(national[:2] + "9" + national[2:])

    keys = {digits}
    for candidate in nationals:
        keys.add(candidate)
        keys.add(BR_COUNTRY_CODE + candidate)

    return sorted(keys)
