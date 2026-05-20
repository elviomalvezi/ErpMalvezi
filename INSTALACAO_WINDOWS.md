# Instalação em Windows Server

## Pré-requisitos

- Windows Server 2019 / 2022 (ou Windows 10/11 Pro)
- 4 GB RAM mínimo (8 GB recomendado)
- 20 GB de espaço em disco
- Acesso à internet para baixar as imagens Docker (só na primeira vez)

---

## 1. Instalar Docker Desktop

1. Baixe o instalador em: **https://www.docker.com/products/docker-desktop/**
2. Execute o instalador e marque **"Use WSL 2 instead of Hyper-V"** (recomendado)
3. Após a instalação, reinicie o servidor
4. Abra o Docker Desktop e aguarde o ícone ficar verde (Docker running)

**Verificar instalação** — abra o PowerShell e execute:
```powershell
docker --version
docker compose version
```

---

## 2. Copiar os arquivos para o servidor

Copie toda a pasta `AppFinanceiro` para o servidor. Sugestão de destino:
```
C:\AppFinanceiro\
```

---

## 3. Criar o arquivo de configuração

Na pasta `C:\AppFinanceiro`, copie o arquivo de exemplo e edite:

```powershell
cd C:\AppFinanceiro
Copy-Item .env.prod.example .env.prod
notepad .env.prod
```

**Campos obrigatórios a alterar no `.env.prod`:**

| Campo | O que colocar |
|---|---|
| `POSTGRES_PASSWORD` | Senha forte para o banco (ex: `MinhaS3nhaF0rte!`) |
| `DATABASE_URL` | Troque `TROQUE_SENHA_FORTE_AQUI` pela mesma senha acima |
| `SECRET_KEY` | Chave aleatória — gere com o comando abaixo |
| `MINIO_ROOT_PASSWORD` | Senha para o storage de arquivos |
| `STORAGE_SECRET_KEY` | A mesma senha do MinIO acima |
| `SMTP_*` | Dados do e-mail da empresa (opcional no início) |

**Gerar a SECRET_KEY:**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```
*(se não tiver Python, use qualquer string longa e aleatória de 64 caracteres)*

---

## 4. Construir e subir os containers

Abra o PowerShell **na pasta `C:\AppFinanceiro`**:

```powershell
cd C:\AppFinanceiro

# Construir as imagens (somente na primeira vez ou após atualização)
docker compose -f docker-compose.prod.yml build

# Subir todos os serviços em segundo plano
docker compose -f docker-compose.prod.yml up -d
```

O primeiro `build` demora alguns minutos pois baixa as dependências. As próximas vezes são rápidas.

---

## 5. Verificar se está funcionando

```powershell
# Ver status de todos os containers
docker compose -f docker-compose.prod.yml ps

# Todos devem aparecer como "running" ou "healthy"
```

Abra o navegador e acesse:
```
http://localhost
```

O app deve abrir. Se estiver acessando de outro computador na rede:
```
http://IP-DO-SERVIDOR
```

---

## 6. Criar o usuário administrador

Após o primeiro acesso, crie o admin via linha de comando:

```powershell
docker compose -f docker-compose.prod.yml exec backend python -c "
import asyncio
from app.core.database import get_engine
from app.modules.usuario.service import UsuarioService
# Ou use o endpoint /api/v1/auth/setup-admin se disponível
print('Ver documentação do endpoint de setup')
"
```

*Consulte a documentação interna do projeto para o endpoint de criação do primeiro usuário.*

---

## 7. Iniciar automaticamente com o Windows

Para que o app suba automaticamente quando o servidor reiniciar:

1. Abra o **Agendador de Tarefas** (Task Scheduler)
2. Clique em **"Criar Tarefa Básica"**
3. Nome: `AppFinanceiro - Docker`
4. Gatilho: **"Quando o computador iniciar"**
5. Ação: **"Iniciar um programa"**
   - Programa: `powershell.exe`
   - Argumentos: `-WindowStyle Hidden -Command "cd C:\AppFinanceiro; docker compose -f docker-compose.prod.yml up -d"`
6. Em **"Condições"**, desmarque "Iniciar somente se o computador estiver ligado à corrente"
7. Em **"Configurações"**, marque "Executar mesmo se o usuário não estiver conectado"

> **Alternativa:** O Docker Desktop tem opção nativa "Start Docker Desktop when you log in" nas configurações — se marcada, os containers com `restart: unless-stopped` sobem automaticamente.

---

## Comandos do dia a dia

```powershell
cd C:\AppFinanceiro

# Ver logs em tempo real
docker compose -f docker-compose.prod.yml logs -f

# Ver logs só do backend
docker compose -f docker-compose.prod.yml logs -f backend

# Parar tudo
docker compose -f docker-compose.prod.yml down

# Reiniciar um serviço específico
docker compose -f docker-compose.prod.yml restart backend

# Atualizar o app (após copiar novos arquivos)
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## Backup do banco de dados

Execute este comando para criar um backup:

```powershell
# Criar backup (salva em C:\AppFinanceiro\backups\)
$data = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path C:\AppFinanceiro\backups
docker exec appfin_postgres pg_dump -U app_financeiro_user app_financeiro `
  > "C:\AppFinanceiro\backups\backup_$data.sql"
```

**Automatizar backup diário com Agendador de Tarefas:**
- Crie um arquivo `C:\AppFinanceiro\backup.ps1` com o comando acima
- Agende para rodar todo dia às 02:00

---

## Serviços e portas

| Serviço | Porta | Acesso |
|---|---|---|
| App (frontend + API) | **80** | `http://IP-DO-SERVIDOR` |
| MinIO Console (storage) | **9001** | `http://IP-DO-SERVIDOR:9001` |
| PostgreSQL | 5432 | Somente interno |

---

## Solução de problemas

**Container não sobe:**
```powershell
docker compose -f docker-compose.prod.yml logs backend
```

**Erro de banco de dados:**
```powershell
# Verificar se o postgres está saudável
docker compose -f docker-compose.prod.yml ps postgres
```

**Porta 80 ocupada (IIS ativo no servidor):**
```powershell
# Parar o IIS
Stop-Service W3SVC
Set-Service W3SVC -StartupType Disabled

# Ou mudar a porta do app no docker-compose.prod.yml:
# ports: - "8080:80"
# e acessar em http://IP-DO-SERVIDOR:8080
```

**Reiniciar tudo do zero (mantém dados):**
```powershell
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

**Apagar tudo incluindo banco (cuidado!):**
```powershell
docker compose -f docker-compose.prod.yml down -v
```
