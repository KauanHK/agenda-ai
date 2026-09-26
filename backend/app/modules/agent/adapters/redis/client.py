"""Cliente Redis assíncrono compartilhado.

Um Redis, dois usos independentes (checkpointer do LangGraph e cache de sessão),
prefixos separados. O DB é escolhido na própria `AGENT_REDIS__URL` (`.../1`, por
exemplo) para não dividir keyspace com outro serviço.
"""

from redis.asyncio import Redis


def build_redis_client(url: str) -> Redis:
    """Cria o cliente Redis assíncrono a partir da URL de conexão."""
    return Redis.from_url(url)
