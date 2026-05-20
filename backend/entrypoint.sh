#!/bin/sh
set -e

echo "Aguardando o banco de dados..."
until python -c "
import asyncio, asyncpg, os
async def check():
    await asyncpg.connect(os.environ['DATABASE_URL'].replace('postgresql+asyncpg', 'postgresql'))
asyncio.run(check())
" 2>/dev/null; do
  sleep 2
done

echo "Banco disponivel. Executando migrations..."
alembic upgrade head

echo "Iniciando servidor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
