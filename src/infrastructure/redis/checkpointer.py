"""Checkpointer do LangGraph sobre Redis.

Ao contrário do cache de sessão, uma falha de Redis aqui **não** é engolida:
perder o histórico muda o comportamento do agente de forma visível ao cliente, e
o runner traduz isso em `ConversationStateError`.

O `thread_id` de cada conversa é o `ConversationRef.thread_id`
(`telegram:{chat_id}`). O TTL (`CONVERSATION__TTL_MINUTES`, default 24 h) é
aplicado pelo próprio saver e renovado a cada acesso: o histórico de um
agendamento não tem valor depois de alguns dias, e expirar não é erro — a próxima
mensagem começa uma conversa nova.
"""

from contextlib import AbstractAsyncContextManager

from langgraph.checkpoint.redis.aio import AsyncRedisSaver


def open_conversation_checkpointer(
    redis_url: str,
    *,
    ttl_minutes: int,
) -> AbstractAsyncContextManager[AsyncRedisSaver]:
    """Abre o checkpointer Redis com os índices criados e o TTL configurado.

    Devolve um context manager assíncrono: o `__aenter__` roda o `asetup()` (cria
    os índices) e o `__aexit__` fecha a conexão. Instancie-o uma vez, no lifespan
    da aplicação.
    """
    return AsyncRedisSaver.from_conn_string(
        redis_url,
        ttl={"default_ttl": ttl_minutes, "refresh_on_read": True},
    )
