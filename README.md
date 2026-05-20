# App Financeiro — Ambiente Local

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução.

## Primeira vez

```bash
# 1. Copie o arquivo de variáveis de ambiente
cp .env.example .env

# 2. Suba os containers em segundo plano
docker compose up -d
```

## Operações do dia a dia

```bash
# Subir
docker compose up -d

# Parar (mantém os volumes/dados)
docker compose down

# Parar e remover volumes (apaga todos os dados locais)
docker compose down -v

# Ver status e saúde dos containers
docker compose ps

# Ver logs em tempo real
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f postgres
```

## Serviços e como acessar

| Serviço | URL / Endereço | Credenciais |
|---------|---------------|-------------|
| **PostgreSQL** | `localhost:5432` | Usuário/senha definidos no `.env` |
| **MinIO Console** (web) | http://localhost:9001 | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| **MinIO API** (S3) | http://localhost:9000 | Mesmas credenciais do console |
| **MailHog** (web) | http://localhost:8025 | Sem autenticação |
| **MailHog** (SMTP) | `localhost:1025` | Sem autenticação |

## Próximos passos

Após o ambiente subir com `docker compose ps` mostrando todos os serviços `healthy` (ou `running`):

1. Iniciar o scaffolding do backend (`backend/`)
2. Iniciar o scaffolding do frontend (`frontend/`)
