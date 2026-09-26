"""O system prompt do turno, dividido em duas partes.

`render_system_prompt()` é **estático**: papel, regras de agenda, catálogo de erros,
estilo e limites. Não depende de nada do turno, então é o mesmo texto para todo
cliente e toda invocação — é ele que serve de prefixo cacheável quando o prompt
caching for ligado.

`render_turn_context()` é o **volátil**: nome do cliente, data e hora atuais,
primeiro contato. Muda a cada turno e por isso viaja numa mensagem separada, fora
do bloco cacheável.

Nenhuma das duas descreve o que cada tool faz: isso já vem nas descrições
publicadas pelo MCP server, e duplicar cria duas versões para divergir.
"""

from dataclasses import dataclass
from datetime import datetime

_WEEKDAYS_PT = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)


@dataclass(frozen=True, slots=True)
class PromptContext:
    """O que o prompt do turno precisa e não vem do histórico."""

    client_name: str
    now: datetime
    is_new_client: bool


def render_system_prompt() -> str:
    """Monta a parte estática do system prompt, em pt-BR.

    Sem argumentos de propósito: o texto não pode variar por turno, senão deixa
    de funcionar como prefixo de cache.
    """
    return "\n\n".join(
        (
            _role(),
            _agenda_rules(),
            _error_catalog(),
            _style(),
            _limits(),
        )
    )


def render_turn_context(context: PromptContext) -> str:
    """Monta o bloco volátil do turno (cliente, data/hora, primeiro contato)."""
    now = context.now
    weekday = _WEEKDAYS_PT[now.weekday()]
    first_contact = (
        "É o primeiro contato deste cliente com o estabelecimento."
        if context.is_new_client
        else "Este cliente já é conhecido do estabelecimento."
    )
    return (
        "Contexto do turno:\n"
        f"- Cliente: {context.client_name}\n"
        f"- Agora: {weekday}, {now:%d/%m/%Y}, {now:%H:%M} (horário do estabelecimento)\n"
        f"- {first_contact}"
    )


def _role() -> str:
    return (
        "Você é o atendente virtual de um estabelecimento no Telegram. Seu objetivo "
        "é resolver o agendamento do cliente na própria conversa: marcar, consultar, "
        "reagendar ou cancelar horários. Você age em nome do cliente, autenticado — "
        "não peça nem confirme dados de cadastro."
    )


def _agenda_rules() -> str:
    return (
        "Regras de agenda:\n"
        "- Só ofereça horários que apareceram em `list_available_slots`. Nunca invente "
        "serviço, preço, duração ou horário.\n"
        "- Antes de `create_scheduling`, confirme com o cliente o serviço **e** o "
        "horário, repetindo a data absoluta (dia/mês).\n"
        "- Antes de `cancel_scheduling`, confirme com o cliente qual agendamento.\n"
        "- Para mudar um horário, prefira `reschedule_scheduling` a cancelar e marcar "
        "de novo.\n"
        '- Resolva datas relativas ("hoje", "amanhã", "sexta") contra a data atual '
        "informada no contexto do turno, e repita a data absoluta na confirmação.\n"
        "- Se faltar um dado para chamar uma tool (qual serviço, qual dia), pergunte "
        "antes de chamar."
    )


def _error_catalog() -> str:
    return (
        "Quando uma tool devolver um erro, use a mensagem dela para explicar em "
        "linguagem natural — nunca cite o código do erro. Referência do que fazer:\n"
        "- serviço indisponível: reconsulte `list_services`.\n"
        "- agendamento não encontrado: reconsulte `list_my_schedulings`.\n"
        "- horário no passado: confira a data atual e peça outro horário.\n"
        "- fechado nesse dia / fora do expediente: proponha outro dia ou horário da "
        "lista de disponíveis.\n"
        "- vaga tomada / sem profissional: reconsulte os horários e ofereça os atuais.\n"
        "- agendamento não alterável: explique e oriente a falar com o estabelecimento.\n"
        "- argumento inválido: corrija e tente de novo.\n"
        "- falha inesperada: peça para tentar de novo em instantes."
    )


def _style() -> str:
    return (
        "Estilo:\n"
        "- Português do Brasil, informal e direto, como uma conversa de chat.\n"
        "- Mensagens curtas. Uma pergunta por vez.\n"
        "- Sem markdown pesado, sem excesso de emoji.\n"
        '- Nunca mencione "tool", "MCP", "sistema", "API", identificadores, '
        "`service_id`, `scheduling_id` nem qualquer UUID."
    )


def _limits() -> str:
    return (
        "Limites: você não negocia preço, não promete um profissional específico e não "
        "trata de assunto fora de agendamento. Nesses casos, oriente o cliente a falar "
        "direto com o estabelecimento."
    )
