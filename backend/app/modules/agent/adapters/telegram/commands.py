"""Comandos do bot, tratados antes do agente.

`/start` e `/reset` limpam o histórico e respondem com um texto fixo — a
mensagem de boas-vindas é a primeira impressão e não vale gastar uma chamada de
modelo com ela. Qualquer outro `/x` segue para o agente como texto normal.
"""

import re

_COMMAND = re.compile(r"^/([A-Za-z0-9_]+)(?:@[A-Za-z0-9_]+)?(?=\s|$)")

RESET_COMMANDS = frozenset({"start", "reset"})

WELCOME_MESSAGE = (
    "Oi! Eu cuido da agenda aqui pelo Telegram. "
    "Me diz o que você precisa: marcar, remarcar, consultar ou cancelar um horário."
)
RESET_MESSAGE = "Pronto, recomecei do zero. O que você precisa?"


def match_command(text: str) -> str | None:
    """Extrai o nome do comando (sem a barra, em minúsculas), ou `None`.

    Aceita o sufixo `@nomedobot` que o Telegram anexa em grupos, mesmo o canal
    sendo só privado nesta fase.
    """
    found = _COMMAND.match(text.strip())
    return found.group(1).lower() if found else None
