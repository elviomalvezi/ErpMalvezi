#!/bin/sh
# Backup diário do PostgreSQL do App Financeiro, com rotação.
# Roda na VM de produção via cron. O pg_dump é executado dentro do container
# pelo socket local (sem senha em arquivo). Com os anexos agora no banco (BYTEA),
# este dump cobre TODO o estado da aplicação.
set -eu

BACKUP_DIR=/opt/appfinanceiro/backups
CONTAINER=appfin_postgres
DB_USER=app_financeiro_user
DB_NAME=app_financeiro
RETENTION_DAYS=14
MIN_BYTES=1000  # dump menor que isso é considerado corrompido/vazio

mkdir -p "$BACKUP_DIR"
TS=$(date +%Y%m%d_%H%M%S)
DEST="$BACKUP_DIR/${DB_NAME}_${TS}.sql.gz"

docker exec "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --format=plain | gzip > "$DEST"

# Proteção contra backup vazio/curto (ex.: container fora do ar).
SIZE=$(stat -c%s "$DEST" 2>/dev/null || echo 0)
if [ "$SIZE" -lt "$MIN_BYTES" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERRO: backup vazio/curto ($SIZE bytes) em $DEST" >&2
    rm -f "$DEST"
    exit 1
fi

# Rotação: remove dumps com mais de RETENTION_DAYS dias.
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -type f -mtime +"$RETENTION_DAYS" -delete

echo "$(date '+%Y-%m-%d %H:%M:%S') Backup OK: $DEST ($(du -h "$DEST" | cut -f1))"
