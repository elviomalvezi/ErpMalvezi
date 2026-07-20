FROM python:3.12-slim

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Copia o código
COPY . .

# Script de entrypoint: roda migrações e sobe o servidor
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Roda como usuário sem privilégios (não-root). /app precisa ser gravável para a
# pasta de mídia (anexos/logos) criada em runtime pelo LocalStorageProvider.
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
