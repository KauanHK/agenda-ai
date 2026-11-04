#!/bin/sh
# Backup diário do Postgres: pg_dump comprimido em /backups, com expurgo por
# idade. Roda no container `backup` do compose.
#
# Restaurar (na VPS, com a stack de pé):
#
#   docker compose stop api worker beat agent mcp
#   gunzip -c backups/<arquivo>.sql.gz \
#     | docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
#   docker compose start api worker beat agent mcp
#
# O dump é um .sql.gz (e não um -Fc): restaura com psql puro, sem depender da
# versão do pg_restore, e dá para inspecionar o conteúdo antes de aplicar.
#
# ATENÇÃO: isto é cópia local, na mesma máquina do banco. Protege contra erro de
# operação e migração ruim, não contra perda da VPS.
set -eu
# Sem isto, `pg_dump | gzip` herda o status do gzip: um pg_dump que nem conecta
# vira um "backup" vazio, gravado e anunciado como válido.
set -o pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
# 6h UTC = 3h em Brasília.
BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-0 6 * * *}"

export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD não definido}"

run_backup() {
    mkdir -p "$BACKUP_DIR"
    file="$BACKUP_DIR/${POSTGRES_DB}_$(date -u +%Y%m%dT%H%M%SZ).sql.gz"

    # Escreve em .part e só renomeia no fim: um dump interrompido nunca fica
    # parecendo um backup válido.
    if ! pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        | gzip > "${file}.part"; then
        echo "backup: FALHOU ao gerar $file" >&2
        rm -f "${file}.part"
        return 1
    fi
    mv "${file}.part" "$file"
    echo "backup: $file ($(du -h "$file" | cut -f1))"

    deleted=$(find "$BACKUP_DIR" -name "${POSTGRES_DB}_*.sql.gz" \
        -mtime "+${BACKUP_RETENTION_DAYS}" -print -delete | wc -l)
    echo "backup: expurgo removeu $deleted arquivo(s) com mais de ${BACKUP_RETENTION_DAYS}d"
}

case "${1:-schedule}" in
    once)
        run_backup
        ;;
    schedule)
        # `sh /backup.sh`, e não `/backup.sh`: o arquivo chega sem bit de execução
        # e o crond falharia com "Permission denied" todo dia.
        cat > /etc/crontabs/root <<EOF
$BACKUP_SCHEDULE sh /backup.sh once >> /proc/1/fd/1 2>&1
EOF
        echo "backup: agendado '$BACKUP_SCHEDULE' (UTC), retenção ${BACKUP_RETENTION_DAYS}d"
        exec crond -f -l 2
        ;;
    *)
        echo "uso: $0 [schedule|once]" >&2
        exit 2
        ;;
esac
